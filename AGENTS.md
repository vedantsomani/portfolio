# AGENTS.md — Vedant Somani Portfolio + Freelance Site

Read this file and `SITE_SPEC.md` at the start of every session. `SITE_SPEC.md` is the source of truth for content, design, and motion. If a request conflicts with it, stop and ask.

## Stack (fixed — do not substitute)
- Astro 6, TypeScript strict, content collections (`src/content.config.ts`, Zod schemas), MDX
- Native CSS: custom properties, `@layer`, container queries. No Tailwind, no CSS-in-JS, no UI kits.
- GSAP 3.13+ (all plugins free): ScrollTrigger, SplitText, DrawSVG, Flip. Import per page/island, never globally.
- Native CSS scroll-driven animations (`animation-timeline: view()`) for simple scroll effects.
- OGL for the hero shader (island). Three.js only for the hardware hall (lazy island).
- Astro View Transitions (`<ClientRouter />`).
- Vercel via `@astrojs/vercel`. Static by default; only the contact endpoint runs on demand.
- `@vercel/analytics`, `@vercel/speed-insights`, `@astrojs/sitemap`.
- Forms: Astro Action + Zod → Resend. Honeypot + IP rate limit (5/hour).
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
- Initial JS ≤ 90 KB gz per route. Three.js and GLB files load lazily.
- Images AVIF with JPG fallback; hero ≤ 150 KB; `fetchpriority="high"` only on the LCP image.
- Lighthouse mobile: Performance ≥ 95, Accessibility 100, SEO 100, Best Practices 100.

## Workflow
- Work only in the phase named in the current prompt. Never start the next phase.
- Before coding UI: post a plan (files, components, motion list), then build.
- After each phase: `astro check`, build, Lighthouse mobile on every changed route, screenshots at 375 / 768 / 1440, a self-critique against the spec. Report scores, JS/CSS bytes per route, and TODOs.
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
- Stock photos, AI-generated images, generic device mockups