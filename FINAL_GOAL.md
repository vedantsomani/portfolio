# FINAL_GOAL.md — Finish vedantsomani.tech (portfolio only)

You are finishing my personal engineering portfolio. Read `AGENTS.md`, `SITE_SPEC.md`, and `03_PHASE3_MOTION.md` first. **Where this file conflicts with them, this file wins**, and you update them to match (§8).

Work autonomously. Do not stop to ask me questions. Anything that needs my input becomes a `TODO(vedant)` (visible in dev, hidden in production) and goes in the final report. Never invent facts, metrics, photos, or quotes.

---

## 0. Scope change: portfolio only, no freelancing

- **Audience:** recruiters, research labs, collaborators, future co-founders and investors for a defense-tech startup.
- **Remove:** `/services`, pricing, the process section, "Start a project", budget/company fields, and every freelance phrase. Add `/services → /` as a 301 in `public/_redirects`.
- **Hero headline:** "Flight controllers, autonomy, and secure comms — built from the silicon up."
- **Supporting line:** "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them."
- **CTAs:** primary "See the work" → `/projects`; secondary "Get in touch" → `/contact`. The nav button is "Get in touch".
- **Final CTA field:** "Working on something hard?" plus a "Get in touch" button.

## 1. Content (from SITE_SPEC §6 only)

My inputs are below. Anything left as `<…>` stays `TODO(vedant)`.

```
SETU status: <Concept / Prototype / Validated / Archived>
SETU third spec: <e.g. AUW, motor/prop, flight time>
Saarthi: role <…>, year <…>
Saarthi fusion benchmark lab entry: status <…>, date <…>, one-line result <…>
Third lab entry: <PRAHARI shield sim / VAJRA ProVerif model / ESP32 MAVLink bridge>, status <…>, date <…>, result <…>
GitHub: <URL>   LinkedIn: <URL>
```

- **Collections:** build `projects` and `lab` exactly as in `02_PHASE2_CONTENT.md` §1, including the refinement that fails the build when `restricted && repoUrl`.
- **Projects** (engineering template): `saarthi` (flagship), `prahari` (restricted), `vajra` (restricted). No client-case template in production. Delete the client-case placeholder.
- **Lab:** `skynet-setu`, `saarthi-fusion-benchmark`, plus the third entry above if given. Hide any entry that has no status in production.
- **About:** photo placeholder, then 3 short paragraphs (who I am; why hardware and software together; what I'm building toward). Include roles: Head of Research at Technotix BU and at BC3; core member of BURS. Link the résumé at `/resume.pdf` (a `TODO(vedant)` file). No skill logos.
- **Restricted projects** (PRAHARI, VAJRA, SKYNET): architecture and results only. No control laws, protocol internals, key handling, or repo links.

## 2. Pages

`/`, `/projects`, `/projects/[slug]`, `/lab`, `/lab/[slug]`, `/about`, `/contact`, and 404.

**Home order:**
1. Hero (X-ray lens)
2. Selected work (Saarthi large, SETU small)
3. Hardware hall (full-bleed oxblood field)
4. Lab preview (hidden until ≥1 entry has a status and a result)
5. Final CTA field

## 3. Contact form

- **Fields:** Name, Email, Reason (Internship / Research collaboration / Hardware project / Other), Message. Honeypot kept. `?reason=` prefill.
- **Subject:** "New message — {name} ({reason})". Plain-text and HTML bodies, one field per line, then `Message:`, with input escaped.
- **Recipient:** `CONTACT_TO_EMAIL` if set, else `hello@vedantsomani.tech`.
- **Sender:** `Vedant Somani <hello@vedantsomani.tech>`. Never `resend.dev` in production.
- **`wrangler.jsonc`:** add `"keep_vars": true`, so deploys never wipe dashboard variables.
- Do not touch secrets, DNS, or the Cloudflare/Resend dashboards.

## 4. Visual system (keep what exists; apply these rules)

- **Tokens:** as in `tokens.css`. `--oxblood-hi` `#E25964` is final.
- **Red** appears only on buttons, focus rings, and error text. Prose links are `--ink` with an `--ink-2` underline and turn `--oxblood-hi` on hover. The availability dot is `--ink-2`.
- **Full-bleed oxblood fields:** Hardware hall, final CTA, case-study headers, Contact header.
- **Placeholders:** generated PCB-pattern placeholders stay until real photos land in `src/assets/inbox/`. If files exist there, crop them to each slot's aspect ratio, export AVIF + JPG, write real alt text, and use them.
- **Photo brief for `ASSETS.md`:** the hero shot has a dark bench on the left third and all 4 mounting holes visible.

## 5. Motion (Phase 3 spec, all of it)

Implement `03_PHASE3_MOTION.md` §1–§6 in full:
1. **X-ray lens hero:** OGL shader with velocity radius, decaying trail, noise edge and rim. CSS mask fallback. A scripted pass on mobile. A reduced-motion toggle.
2. **Headline:** one line-masked SplitText reveal, once per session.
3. **Hardware hall:** Three.js, lazy, drag to rotate, carousel, AVIF-sprite fallback. It uses GLB placeholders (a procedural board and a frame mesh) until real GLBs exist in `public/models/`.
4. **Page transitions:** oxblood panel wipe between main routes; shared-element morph from card to case study.
5. **Scroll moments:** exactly three (case-cover clip wipe, left-gutter signal trace, Lab telemetry line). The telemetry uses a placeholder dataset marked `TODO(vedant)` until the CSV exists.
6. **Micro-interactions:** button clip-wipe fill and drawn underline only.

**Rules:**
- Kill and re-init everything on `astro:before-swap` / `astro:page-load`.
- `prefers-reduced-motion` resolves everything to its final state.
- No content lives only inside a canvas.

## 6. SEO and launch-readiness (do not launch)

- **Pre-launch:** keep `PRE_LAUNCH = true`, so production still sends noindex. Make it overridable with a local env var so audits can run with it off.
- **SEO:** per-page title (≤ 60 chars), description (≤ 155), and canonical on `https://vedantsomani.tech`. Generate OG images at build with Satori (tokens + wordmark). Sitemap and `robots.txt`.
- **JSON-LD:** `Person` on `/about`, `CreativeWork` on project pages. No `Service`, `Offer`, or reviews.
- **Headers:** security headers in `public/_headers`, with the CSP allowing `static.cloudflareinsights.com` and `cloudflareinsights.com`.
- **Analytics:** Cloudflare Web Analytics beacon, gated on `PUBLIC_CF_BEACON_TOKEN`. `track()` stays a no-op with the event names updated for the new scope (drop service and pricing events; add `hero_see_work`, `hero_get_in_touch`).

## 7. Budgets (merge blockers, from AGENTS.md)

- **Lighthouse mobile** (with `PRE_LAUNCH` off locally): Performance ≥ 95, Accessibility 100, Best Practices 100, SEO 100 on every route except 404.
- **Vitals:** LCP ≤ 2.0 s, CLS ≤ 0.05.
- **Initial JS** ≤ 90 KB gz per route. Three.js and GLBs are not in any initial chunk.
- **Hero photo:** ≤ 150 KB desktop and ≤ 60 KB mobile source. On mobile the headline is the LCP element.

## 8. Docs

Update `SITE_SPEC.md` and `AGENTS.md` to the new scope: positioning, audience, IA, contact fields, the red-usage rule, `keep_vars`, and `PRE_LAUNCH`. Mark `01`–`04` phase files as historical at the top of each.

## 9. Acceptance checks (run all; print the output of each in this session)

1. `npm run check`: `astro check`, ESLint and Prettier all exit 0.
2. `npm run build` exits 0.
3. Forbidden-string scan over `dist/`: zero matches for `TODO`, `Start a project`, `₹`, `/services"`, `resend.dev`, `pricing`, `budget`. Print the grep command and its empty result.
4. **Route check** against `npm run preview`: print the HTTP status for every route above. Expect 200, 404 for an unknown path, and `/services` → 301 to `/`.
5. **Lighthouse mobile** (PRE_LAUNCH off) for every route: print a table of the four scores, LCP and CLS, all meeting §7.
6. **axe** at 375 and 1440 on every route: print "0 violations" per route.
7. **Bundle report:** initial JS gz per route ≤ 90 KB, and Three.js absent from initial chunks. Print both.
8. **Playwright, JS disabled:** every route renders its main heading, nav, and content. Print the pass list.
9. **Playwright, `reduced-motion`:** there are no running animations on Home or a project page; the hero shows the "Show circuit layout" toggle. Print the result.
10. **Contact form** under `wrangler dev` with a stubbed Resend endpoint: print the captured request, showing the correct from, to, reply-to, subject, and body. A `?reason=internship` prefill works.
11. **Screenshots** at 375, 768 and 1440 for every route, saved to `qa/final/`, plus a written self-critique against the Lando Norris reference and the anti-AI rules in `AGENTS.md`. Fix anything the critique flags, then re-run checks 1–7.
12. **Commit and push to `main`.** Then `curl -sI https://vedantsomani.tech/` (retry for up to 10 min while Cloudflare builds) shows 200 and `x-robots-tag: noindex, nofollow`, and `curl -s https://vedantsomani.tech/` contains "built from the silicon up".
13. **Write `REPORT.md`:** what was built, the final Lighthouse table, bundle sizes, and every remaining `TODO(vedant)` grouped by photos, 3D models, data, content and links. End it with the exact steps for me to launch (set `PRE_LAUNCH = false`, turn off `workers_dev`, re-run Lighthouse).