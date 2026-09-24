PHASE 4 — SEO, analytics, QA, launch. Read `AGENTS.md` and `SITE_SPEC.md` first; both are binding. Phases 1–3 are done.

## 1. SEO
- A `SEO.astro` component: title, description, canonical, OG/Twitter tags on every route. Titles ≤ 60 chars, descriptions ≤ 155 chars, all unique.
- OG images generated at build with Satori: `--bg` field, oxblood block, wordmark, page title in Archivo expanded. One per project.
- `@astrojs/sitemap`, `robots.txt`, a canonical domain `TODO(vedant)`, and a www → apex redirect. Workers static assets only apply `_redirects` rules to paths on the same host, so do the host-level www → apex redirect as a Cloudflare Redirect Rule (or a `www` route to the Worker that returns 301). Path redirects go in `public/_redirects`.
- JSON-LD: `Person` on /about, `Service` + `Offer` (price ranges from spec §5) on /services, `CreativeWork` on case studies. Only content visible on the page. No review or rating markup.

## 2. Analytics
- Page views: the Cloudflare Web Analytics beacon (already in `BaseLayout`, needs `PUBLIC_CF_BEACON_TOKEN`). No cookies, no consent banner.
- Custom events: every event in `SITE_SPEC.md §7` already goes through `track()` in `src/lib/track.ts` (currently a no-op). Backend is TBD at the start of this phase; candidate: Workers Analytics Engine behind a first-party `/api/e` endpoint (on-demand route, `navigator.sendBeacon`, no third-party script), with `lead_submit` also written server-side from the contact Action so no-JS submissions count. Include props: `page`, `project` (when relevant), `type`/`budget` on `lead_submit` (never names or emails). Rate-limit or validate `/api/e` so it can't be used to flood the dataset.
- Real-user performance: Cloudflare Web Analytics Core Web Vitals (replaces Speed Insights).
- Write a `METRICS.md` explaining where each event fires and the funnel: commercial page → contact_open → form_start → lead_submit.

## 3. Accessibility
- axe-core run on every route (Playwright + `@axe-core/playwright`): zero violations.
- Keyboard-only walkthroughs: nav, hero toggle, hardware hall (arrow keys rotate), filters, form.
- Screen-reader check (VoiceOver): hero, case studies, form errors.
- Reduced motion: record every route with it on and confirm no movement.

## 4. QA matrix
- Browsers: Chrome, Safari (macOS + iOS), Firefox, Samsung Internet.
- Widths: 320, 375, 414, 768, 1024, 1440, 1920.
- Conditions: JS off, WebGL off, slow 4G, `saveData`, back/forward navigation during transitions.
- Visual regression: Playwright screenshots committed as a baseline.

## 5. Performance final pass
Lighthouse mobile on every route (targets in `AGENTS.md`). Bundle analysis per route. Fix or cut anything over budget and report what you cut.

## 6. Launch
- Production domain on Cloudflare Workers (custom domain on the Worker), HTTPS, security headers in `public/_headers` for static pages and set in the Worker response for `/contact` (CSP allowing only self + `https://static.cloudflareinsights.com` for the beacon script and `https://cloudflareinsights.com` for its reports, HSTS, Referrer-Policy, Permissions-Policy).
- Google Search Console: verify the domain and submit the sitemap. TODO(vedant): account.
- Resend: SPF/DKIM/DMARC on the sending domain. Send a live form test.
- `LAUNCH.md`: final checklist, all remaining TODOs, and how to add a new project (the MDX + assets workflow).

## Report back
Lighthouse table for all routes · axe results · QA matrix pass/fail · production URL · remaining TODOs.
