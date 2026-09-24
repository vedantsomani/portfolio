> **Historical.** Superseded by `FINAL_GOAL.md` (portfolio only, no freelancing) and the updated `SITE_SPEC.md` / `AGENTS.md`. Kept as a record of how the site was built; do not follow it where it disagrees with those files.

You are the lead engineer and designer on my portfolio + freelance site. Read `AGENTS.md` and `SITE_SPEC.md` in full before doing anything. They are binding.

Reference for craft level: landonorris.com (OFF+BRAND, Awwwards Site of the Year 2025): an owned color used boldly, real objects, sharp motion. The site must not look AI-generated; `AGENTS.md` lists the tells to avoid.

## PHASE 0 — Design plan (no code; stop for approval)
Deliver in chat:
1. **Tokens:** derive `--surface`, `--ink`, `--ink-2`, `--rule`, `--oxblood-hi` from `#14100E` and `#5A1E14`. Show the WCAG ratio for every text/background pair.
2. **Type scale:** Archivo `wdth` + weight + tracking for display, H1–H3, body, small; the Plex Mono data style. Give px/rem at 375 and 1440.
3. **ASCII wireframes:** Home at 1440 and 375; an engineering case study at 1440; Services at 1440.
4. **Oxblood map:** exactly where the large oxblood fields appear on Home and case studies.
5. **Wordmark placeholder:** describe the PCB-trace "VEDANT" construction (grid, stroke, corner, pad rules).
6. **Self-review:** run through `AGENTS.md` anti-AI rules and list any part of the plan that resembles a generic dev portfolio, what you changed, and why.

Then STOP and wait for "approved".

## PHASE 1 — Foundation (only after approval)
1. `npm create astro@latest` (minimal, TS strict). Install the stack from `AGENTS.md`. Set up ESLint + Prettier + `astro check` in CI (GitHub Actions).
2. `src/styles/`: `tokens.css`, `reset.css`, `base.css`, `layout.css`, `components.css` in `@layer` order.
3. Layout: `BaseLayout.astro` with meta slots, `<ClientRouter />`, skip link, analytics, and a focus-visible style using `--oxblood-hi`.
4. Components: `Nav` (mobile menu as a full-screen panel, focus-trapped, Esc closes), `Footer`, `Wordmark`, `Button`, `Section`, `PriceTable`, `ContactForm`, `Figure` (AVIF + JPG, width/height set, lazy by default).
5. Pages with real spec content + TODOs and **no motion yet**: `/`, `/services`, `/contact`, `404`.
6. The hero right column renders the static photo placeholder only (the lens comes in Phase 3).
7. Contact: Astro Action, Zod validation, honeypot, rate limit (Workers Rate Limiting binding, 5/min per IP), Resend to `TODO(vedant): email`. Inline accessible errors, success state, and a `mailto:` fallback when JS is off.
8. Deploy a Cloudflare Workers preview (`wrangler deploy`, or a preview version via `wrangler versions upload`).
9. QA: Lighthouse mobile on all pages against `wrangler dev` serving the production build (`npm run preview`); screenshots at 375/768/1440; keyboard-only run through nav + form.

## Report back
File tree · Lighthouse scores · JS/CSS bytes per route · preview URL · every `TODO(vedant)` · anything in the spec you think is wrong, with a fix.

Do not start Phase 2.
