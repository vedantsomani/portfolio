# AGENTS.md — Vedant Somani Portfolio + Freelance Site

Read this file and `SITE_SPEC.md` at the start of every session. `SITE_SPEC.md` is the source of truth for content, design, and motion. If a request conflicts with it, stop and ask.

## Stack (fixed — do not substitute)
- Astro 6, TypeScript strict, content collections (`src/content.config.ts`, Zod schemas), MDX
- Native CSS: custom properties, `@layer`, container queries. No Tailwind, no CSS-in-JS, no UI kits.
- GSAP 3.13+ (all plugins free): ScrollTrigger, SplitText, DrawSVG, Flip. Import per page/island, never globally.
- Native CSS scroll-driven animations (`animation-timeline: view()`) for simple scroll effects.
- OGL for the hero shader (island). Three.js only for the hardware hall (lazy island).
- Astro View Transitions (`<ClientRouter />`).
- Cloudflare Workers via `@astrojs/cloudflare` (static assets + Worker). Every page is prerendered except `/contact` and the action endpoint. Config in `wrangler.jsonc`; images optimised at build (`imageService: 'compile'`), no Images or KV bindings. Worker entry `src/worker.ts` wraps the adapter handler and sends `X-Robots-Tag: noindex, nofollow` on every host except `vedantsomani.tech`; `assets.run_worker_first` routes static assets through it too. Canonicals are absolute on `https://vedantsomani.tech`, without `.html` or trailing slashes. Worker name `portfolio` (must match Workers Builds). `workers_dev` and `preview_urls` are on for now; **set `"workers_dev": false` at the Phase 4 launch** once the custom domain serves the site. (Vercel was dropped: Hobby forbids commercial use.)
- Cloudflare Web Analytics beacon (cookieless page views) and `@astrojs/sitemap`. Custom events go through `track()` in `src/lib/track.ts` using the SITE_SPEC §7 names; it is a no-op until an event backend is chosen.
- Forms: Astro Action + Zod → Resend (fetch-based, runs on workerd). Honeypot + Workers Rate Limiting binding `CONTACT_LIMITER` per IP. 5 per minute per IP (the binding supports only 10 s / 60 s windows). Decided: no hourly cap; add Cloudflare Turnstile only if spam appears. Secret via `wrangler secret put RESEND_API_KEY` (locally in `.dev.vars`). Mail goes to `hello@vedantsomani.tech` from `src/data/site.ts`; `CONTACT_TO_EMAIL` is an optional override.
- Fonts self-hosted: `@fontsource-variable/archivo`, `@fontsource/ibm-plex-mono`, Latin subset.

## Hard rules
1. **Never invent content.** No fake clients, testimonials, metrics, logos, ratings, or project details. Use `TODO(vedant): ...` and list every TODO you add at the end of each response.
2. Project facts come only from `SITE_SPEC.md §6`.
3. Defense-adjacent projects (PRAHARI, VAJRA, SKYNET/SETU): architecture and results level only. No control laws, protocol internals, key-handling code, or repo links unless the spec marks them public.
4. Every piece of motion must explain the system, prove capability, or strengthen hierarchy. Otherwise cut it.
5. `prefers-reduced-motion: reduce` → every animation resolves to its final state instantly.
6. The site must be fully usable with JS disabled. No content or navigation lives only inside a canvas.
7. Performance budgets are merge blockers.

## Performance budgets (p75, mid-range Android, 4G throttle)
- LCP ≤ 2.0 s · INP ≤ 200 ms · CLS ≤ 0.05
- Initial JS ≤ 90 KB gz per route. Three.js and GLB files load lazily. The Cloudflare Web Analytics beacon (third-party, deferred) is excluded from this figure but reported separately.
- Images AVIF with JPG fallback. Hero photo ≤ 150 KB desktop source, ≤ 60 KB mobile source (4:3 crop). `fetchpriority="high"` only on the desktop hero (≥ 1024 px, via a media-scoped preload); on mobile the headline is the intended LCP element.
- Lighthouse mobile: Performance ≥ 95, Accessibility 100, SEO 100, Best Practices 100.

## Workflow
- Work only in the phase named in the current prompt. Never start the next phase.
- Before coding UI: post a plan (files, components, motion list), then build.
- After each phase: `astro check`, build, Lighthouse mobile on every changed route (measured against `wrangler dev` serving the production build: `npm run preview`), screenshots at 375 / 768 / 1440, a self-critique against the spec. Report scores, JS/CSS bytes per route, and TODOs.
- If `figma/` frames or a Figma link are provided, implement them exactly (via the Figma MCP `get_design_context`). Don't redesign.
- Conventional commits: `feat:`, `fix:`, `perf:`, `content:`, `style:`.

## Anti-AI-look rules (reject on sight)
- Fade-and-slide-up on every section; word- or character-level text reveals on every heading
- Smooth-scroll libraries (Lenis, Locomotive), scroll hijacking
- Custom cursor site-wide, particles, fake terminal typing, glitch text, magnetic buttons, tilt cards
- ALL-CAPS tracked eyebrow labels above every heading; `A · B · C` meta strings; `→` on every button
- Identical rounded cards; one border-radius everywhere; gradients; drop shadows
- Accenting a single word in a headline with color or italic
- 01/02/03 numbering on content that isn't a real sequence
- Skill-logo walls, "10+ technologies" counters, tech-tag filters
- Monospace anywhere except real data: part numbers, measurements, timestamps, status
- Oxblood used as thin accents everywhere. Use it in large fields or not at all (see spec §3).
- **Red usage rule:** `--oxblood-hi` appears only on buttons, focus rings, and error text (plus link hover). Links are `--ink` with an `--ink-2` underline; status marks are `--ink-2`; `#5A1E14` only as large full-bleed fields (final CTA, Hardware hall, case headers, contact header, transitions).
- Stock photos, AI-generated images, generic device mockups