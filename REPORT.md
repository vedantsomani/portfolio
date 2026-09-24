# REPORT.md — vedantsomani.tech, final build (FINAL_GOAL.md)

The site is now an engineering portfolio only: all freelance material is gone, and the full Phase 3 motion spec is built. It is still **pre-launch**: production sends `X-Robots-Tag: noindex, nofollow` until you flip `PRE_LAUNCH` (launch steps at the end).

## What was built

**Scope change (§0)**
- Deleted `/services`, the price table, the process section, "Start a project", the budget and company fields, the rupee font, and every freelance phrase.
- `/services` and `/services/*` 301 to `/`. The rule is in `public/_redirects` and is also answered in `src/worker.ts`: with `run_worker_first`, the adapter's asset fallback would otherwise follow the 301 and serve `/` as a 200.
- New hero headline, supporting line, and CTAs ("See the work" → `/projects`, "Get in touch" → `/contact`). The nav button reads "Get in touch". The final CTA field reads "Working on something hard?".

**Content (§1)**
- `projects` and `lab` content collections (`src/content.config.ts`), including the Zod refinement that fails the build when `restricted && repoUrl`.
- Projects: `saarthi` (flagship), `prahari` and `vajra` (restricted: architecture and results only, no repo link).
- Lab entries: `skynet-setu` and `saarthi-fusion-benchmark`. Neither has a status yet, so both are hidden in production, and so are the Home lab preview and the `/lab/[slug]` pages.
- No client case exists anywhere.
- About: photo placeholder, three paragraphs, your roles, and a résumé link that appears once `public/resume.pdf` exists.

**Pages (§2)**
- `/`, `/projects`, `/projects/[slug]`, `/lab`, `/lab/[slug]` (built only for entries with a status), `/about`, `/contact`, 404.
- Home order: hero with X-ray lens → selected work (Saarthi large, SETU small) → Hardware hall (oxblood field) → lab preview (gated) → final CTA.

**Contact (§3)**
- Fields: Name, Email, Reason (Internship / Research collaboration / Hardware project / Other), Message.
- Honeypot and rate limiter kept. `?reason=` prefills the reason.
- Subject "New message — {name} ({reason})". Text and HTML bodies with escaped input.
- Recipient: `CONTACT_TO_EMAIL`, falling back to `hello@vedantsomani.tech`. Sender: `Vedant Somani <hello@vedantsomani.tech>`.
- The Resend SDK is replaced by a direct `fetch` to the REST API. `RESEND_API_URL` exists only so QA can point the call at a stub.
- `"keep_vars": true` in `wrangler.jsonc`.

**Visual (§4)**
- The red usage rule is applied: `--oxblood-hi` only on buttons, focus rings, error text, and link hover. Links are ink with an ink-2 underline.
- Generated PCB placeholders for every image slot, including a pixel-aligned X-ray placeholder for the hero.
- `ASSETS.md` holds the photo brief (dark left third, all 4 mounting holes visible) and the drop-in workflow (`src/assets/inbox/`, `public/models/`, `public/data/`).

**Motion (§5)**: all of `03_PHASE3_MOTION` §1–§6.
1. **X-ray lens:** OGL shader with a velocity radius (≤ 1.6×, relaxing in about 600 ms), a ping-pong trail decaying at 0.92 per frame, a simplex-noise edge (about 12 px), and a rim. DPR is capped at 1.5, and the render loop pauses off-screen or in a hidden tab. CSS mask fallback for no WebGL, ≤ 4 cores, or saveData. One scripted Lissajous pass on touch screens, then the lens settles centre-right at 60% radius. Under reduced motion there's a keyboard-operable "Show circuit layout" toggle instead.
2. **Headline:** SplitText line-masked reveal, once per session, 1.3 s total. It's held before first paint with no flash, and a CSS failsafe shows it if JS never runs.
3. **Hardware hall:**
   - Three.js is loaded only when the hall is within one viewport.
   - Drag rotates with inertia; after idling it turns at 6°/s; the wheel never zooms.
   - The carousel swaps objects in 500 ms: the old one scales 1 → 0.85 as the new one comes in from −30°.
   - Arrow keys rotate the object.
   - Without WebGL it falls back to a 24-frame AVIF sprite (`npm run sprites`).
   - It uses procedural placeholder meshes until the GLBs exist.
4. **Transitions:** an oxblood panel wipes between routes (250 ms in, 300 ms out). The project card → case study cover morphs instead, including on back/forward. Reduced motion swaps instantly.
5. **Scroll moments:** the cover clip wipe (CSS `view()` timeline), the left-gutter signal trace (DrawSVG + ScrollTrigger, desktop only; drawn in `--rule-strong` to respect the red rule), and the telemetry line, which draws once (real CSV only).
6. **Micro:** button clip-wipe fill with a 0.98 press; drawn link underline.

Everything is killed on `astro:before-swap` and re-initialised on `astro:page-load`.

**SEO and launch-readiness (§6)**
- `PRE_LAUNCH = true` in `src/worker.ts`. `npm run preview:audit` overrides it locally with `--var PRE_LAUNCH:false`.
- Per-page titles ≤ 60 characters and descriptions ≤ 155 (checked). Canonicals on `https://vedantsomani.tech`.
- Satori OG images: `scripts/og.mjs` runs first in `npm run build`; the output in `public/og/` is committed.
- Sitemap and `robots.txt`.
- JSON-LD: `Person` on `/about`, `CreativeWork` on project pages.
- Security headers in `public/_headers` and on every Worker response. The CSP allows `static.cloudflareinsights.com` and `cloudflareinsights.com`.
- The server bundle is now minified (Astro leaves it readable by default).
- `track()` event names are updated (`hero_see_work`, `hero_get_in_touch` added; service, pricing, and WhatsApp events dropped).

**Docs (§8)**: `SITE_SPEC.md` and `AGENTS.md` are rewritten for the new scope, and `00`–`04` are marked historical.

## Acceptance checks (FINAL_GOAL §9)
All 13 were run in this session. The scripts live in `scripts/qa/` and run against `npm run preview:audit` (`wrangler dev`, production build, `PRE_LAUNCH` off).

| # | Check | Result |
|---|---|---|
| 1 | `npm run check` (astro check + ESLint + Prettier) | exit 0; 0 errors, 0 warnings, 0 hints |
| 2 | `npm run build` | exit 0 |
| 3 | Forbidden strings in `dist/` (`TODO`, `Start a project`, `₹`, `/services"`, `resend.dev`, `pricing`, `budget`) | zero matches (regex and fixed-string passes, including binaries) |
| 4 | Routes | 200 on all 8 routes, 404 on an unknown path, `/services` 301 → `/` |
| 5 | Lighthouse mobile | all routes pass (table below) |
| 6 | axe at 375 and 1440 | 0 violations on all 9 routes (including 404), at both widths |
| 7 | Bundle | initial JS ≤ 42.2 KB gz on every route; Three.js in no initial chunk |
| 8 | Playwright, JS disabled | 9/9 routes render their h1, nav, footer nav, and content |
| 9 | Playwright, reduced motion | 0 running animations on `/` and `/projects/saarthi`; toggle visible and works with Enter and Space |
| 10 | Contact under `wrangler dev` + Resend stub | from, to, reply-to, subject, and both bodies correct; `?reason=internship` prefill works; no-JS POST works too |
| 11 | Screenshots 375/768/1440 + self-critique | 27 PNGs in `qa/final/`, `qa/final/CRITIQUE.md`; 9 issues fixed, then checks 1–7 re-run and passing |
| 12 | Push + live check | see "Live check" below |
| 13 | This report | — |

### Final Lighthouse (mobile, simulated 4G, `PRE_LAUNCH` off)
| Route | Perf | A11y | BP | SEO | LCP | CLS |
|---|---|---|---|---|---|---|
| `/` | 99 | 100 | 100 | 100 | 1.84 s | 0.022 |
| `/projects` | 100 | 100 | 100 | 100 | 1.75 s | 0.000 |
| `/projects/saarthi` | 99 | 100 | 100 | 100 | 1.83 s | 0.014 |
| `/projects/prahari` | 99 | 100 | 100 | 100 | 1.83 s | 0.000 |
| `/projects/vajra` | 99 | 100 | 100 | 100 | 1.85 s | 0.000 |
| `/lab` | 97 | 100 | 100 | 100 | 1.68 s | 0.000 |
| `/about` | 100 | 100 | 100 | 100 | 1.68 s | 0.000 |
| `/contact` | 100 | 100 | 100 | 100 | 1.52 s | 0.000 |

Home LCP varies between runs (1.5–1.99 s seen). On mobile the LCP element is the hero photo, not the headline: at 412 px the full-bleed 4:3 photo covers more area than the headline. It stays inside budget because Home skips the font preload and all CSS is inlined.

### Bundle sizes (gzip)
| Route | Initial JS | Files |
|---|---|---|
| `/` | 42.2 KB | 12 (GSAP core + SplitText, lens controller, hall controller, trace loader, router) |
| `/projects`, `/about`, 404 | 6.9 KB | 7 |
| `/projects/[slug]` | 8.8 KB | 9 |
| `/lab` | 9.0 KB | 10 |
| `/contact` | 11.0 KB | 8 |

Loaded later, never initial:
- OGL lens `gl.js`, 16.2 KB (on idle).
- Three.js stage `stage.js`, 144.3 KB (near the hall).
- GSAP core for pages without the hero, 27.0 KB.
- ScrollTrigger 17.7 KB and DrawSVG 1.9 KB (desktop trace).
- GLTFLoader 13.5 KB and Meshopt 7.1 KB (only if GLBs exist).

There are no GLB files yet.

## Live check
Pushed to `main` (`38429c5`, then the CI fix below). Cloudflare Workers Builds deployed the new build within about 2 minutes.

- **Plain `curl -sI https://vedantsomani.tech/` fails with exit 6 (could not resolve host).** This is not a deploy problem. Cloudflare's authoritative nameservers (`art`/`coraline.ns.cloudflare.com`) return no A or AAAA record for the apex, so no resolver anywhere can find it; `www` does resolve. FINAL_GOAL §3 forbids touching DNS or the dashboards, so this is launch step 1 below.
- **The same request pinned to the Cloudflare edge** (`--resolve vedantsomani.tech:443:104.21.47.86`) returns `HTTP/1.1 200 OK` with `X-Robots-Tag: noindex, nofollow`, the CSP and HSTS headers, and a body containing "built from the silicon up". `/services` returns `301` → `/`.
- **CI:** the first push failed GitHub Actions at `npm run check`. On a cold dependency cache (a fresh checkout), Vite discovered the actions route partway through `astro check` and reloaded. I reproduced it on Linux in WSL. The fix pre-bundles that dependency for the Worker environment (`astro.config.mjs`), and the full CI sequence (lint, format, check, build) now passes on a clean Linux clone.

## Remaining TODO(vedant)
All of these are hidden in production and visible in `npm run dev`.

**Photos** (brief and sizes in `ASSETS.md`)
- Hero photo: Saarthi top-down, dark left third, all 4 mounting holes visible. Plus its alt text (`src/data/site.ts`).
- Hero X-ray: KiCad F.Cu + B.Cu + F.Silkscreen plot, recoloured, aligned to the photo on the mounting holes.
- Cover images for Saarthi, PRAHARI, and VAJRA.
- SETU airframe photo.
- Fusion benchmark plot or bench photo.
- About portrait or workspace photo, plus its alt text.
- Still renders for the hall posters (no-JS view).

**3D models**
- `public/models/saarthi.glb` (KiCad → STEP → Blender) and `public/models/setu.glb` (Fusion 360), each ≤ 2 MB, Meshopt-compressed. Then run `npm run sprites`.

**Data**
- `public/data/fusion-benchmark.csv`, the real Saarthi IMU fusion benchmark (first two numeric columns are plotted). Until it exists, the Lab telemetry plot is hidden in production.

**Content**
- Saarthi: role, year, constraints, bench setup, measurements, failures and iterations.
- PRAHARI: status, role, year, and publishable constraints, setup, results, and iterations. Also confirm the architecture diagram's grouping.
- VAJRA: role, year, and publishable constraints, setup, results, and iterations.
- SETU: status (Concept / Prototype / Validated / Archived), date, one-line result, and a third verified spec (e.g. AUW, motor/prop, flight time).
- Saarthi fusion benchmark: status, date, one-line result.
- Third lab entry (PRAHARI shield sim / VAJRA ProVerif model / ESP32 MAVLink bridge): status, date, result. Not created, since none was given.
- About: confirm the wording of the three paragraphs, especially "I'm building toward defence technology…".
- Final "VEDANT" wordmark SVG (placeholder in `src/lib/wordmark.js`).
- Analytics: choose an event backend for `track()` (a no-op for now), and set `PUBLIC_CF_BEACON_TOKEN` (Cloudflare Web Analytics).

**Links**
- `public/resume.pdf`. The About link appears once it exists.
- Saarthi repository: decide on visibility; set `repoUrl` in `saarthi.mdx` if it goes public.
- GitHub and LinkedIn: set in `src/data/site.ts` as `github.com/vedantsomani` and `linkedin.com/in/vedantsomani12`. Confirm these are the right profiles; the FINAL_GOAL inputs left them blank.

## Launch steps (for you)
1. **Make the apex resolve.** When checked on 2026-09-25, Cloudflare's authoritative nameservers had **no A/AAAA record for `vedantsomani.tech`**. Only `www` resolved. The Worker does serve the apex when the Cloudflare edge is reached directly. In the dashboard, open Workers & Pages → `portfolio` → Settings → Domains & Routes, and add `vedantsomani.tech` as a Custom Domain (which creates the DNS record). Or add a proxied DNS record for the apex. I did not touch DNS or the dashboards.
2. In `src/worker.ts`, set `const PRE_LAUNCH = false;`.
3. In `wrangler.jsonc`, set `"workers_dev": false` (and `"preview_urls": false` if you don't want preview URLs indexed or reachable).
4. Commit and push to `main`. Workers Builds deploys it.
5. Check the headers: `curl -sI https://vedantsomani.tech/` should show **no** `x-robots-tag`, and `curl -sI https://portfolio.<account>.workers.dev/` (if still enabled) should still show `noindex, nofollow`.
6. Re-run Lighthouse against production: `BASE=https://vedantsomani.tech node scripts/qa/lighthouse.mjs`.
7. Then:
   - Verify the domain in Google Search Console and submit `https://vedantsomani.tech/sitemap-index.xml`.
   - Set `PUBLIC_CF_BEACON_TOKEN`.
   - Send one live test through the contact form.
