# SITE_SPEC.md — Vedant Somani: engineering portfolio

Source of truth for content, design, and motion. Updated to `FINAL_GOAL.md` (portfolio only, no freelancing). Where the phase files `01`–`04` disagree with this file, this file wins; they are historical.

## 1. Positioning
A personal engineering portfolio. No freelance offer, pricing, or process.

- Headline: "Flight controllers, autonomy, and secure comms — built from the silicon up."
- Supporting: "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them."
- CTAs: "See the work" → `/projects` (primary) · "Get in touch" → `/contact` (secondary). The nav button is "Get in touch".
- Final CTA field: "Working on something hard?" + "Get in touch".

Audience: recruiters, research labs, collaborators, and future co-founders and investors for a defence-tech startup.
Test for every page: understandable in 10 s, credible in 30 s, contactable in 60 s.

## 2. Information architecture
```
/                    Home: hero (X-ray lens) → selected work → hardware hall → lab preview → final CTA
/projects            Engineering projects (no filter: one kind in production)
/projects/[slug]     Engineering case study
/lab                 Hardware hall + telemetry + build log (entries grouped by status)
/lab/[slug]          Lab entry (only entries with a status are built in production)
/about               Photo, three paragraphs, roles, résumé link
/contact             Form + email
/resume.pdf          TODO(vedant): the link appears once public/resume.pdf exists
404                  Custom, with links to Projects, Contact, Home
/services            301 → / (retired)
```
Home's lab preview stays hidden until at least one lab entry has a status and a result.

## 3. Design system
| Token | Value | Use |
|---|---|---|
| `--bg` | `#14100E` | Canvas |
| `--surface` | `#1E1916` | Panels |
| `--ink` | `#F2EBE4` (16.0:1 on bg) | Primary text |
| `--ink-2` | `#A99D93` (7.1:1 on bg) | Secondary text, status marks |
| `--rule` / `--rule-strong` | `#352C27` / `#75675E` | Structural lines / input borders, the signal trace |
| `--oxblood` | `#5A1E14` | Large full-bleed fields only |
| `--oxblood-hi` | `#E25964` (5.27:1 on bg), final | Buttons, focus rings, error text, link hover |

**Red usage rule**
- `--oxblood-hi` appears only on buttons, focus rings, and error text, plus the link hover colour. Button labels are `--bg` (5.27:1).
- Prose links are `--ink` with an `--ink-2` underline; on hover a currentColor underline draws in and the text turns `--oxblood-hi` (`--ink` on oxblood fields, where oxblood-hi is only 3.59:1).
- Status marks (the availability dot, status labels) are `--ink-2`.
- `--oxblood` `#5A1E14` only as large full-bleed fields: Hardware hall (Home), final CTA, case-study and lab-entry headers, Contact header, page-transition panel. Never on small text.
- Imagery is exempt: the X-ray layer is copper drawn in `--oxblood-hi`, as the real KiCad plot will be.
- Contrast ratios for every pair are in `src/styles/tokens.css`.

**Type**: Archivo variable (display `wdth` 125, weight 800, tight tracking; body `wdth` 100, 17–18 px, measure ≤ 70ch). IBM Plex Mono for real data only (part numbers, measurements, dates, status). Sentence case everywhere.

**Surface & imagery**: no gradients, no shadows, square corners. Real photos > real CAD/3D > diagrams > screen recordings. Never stock or AI images. Generated PCB-pattern placeholders stay until real files land (see `ASSETS.md`). Wordmark: "VEDANT" in PCB-trace geometry (placeholder; TODO(vedant): final SVG). Grid: 12 columns, 1280 max, fluid to 320.

## 4. Motion system (full spec: `03_PHASE3_MOTION.md` §1–§6, all implemented)
1. **Hero X-ray lens**: OGL shader (velocity-reactive radius up to 1.6×, decaying trail, simplex-noise edge, `--oxblood-hi` rim), CSS mask fallback (no WebGL, ≤ 4 cores, or saveData), one scripted Lissajous pass on touch, "Show circuit layout" toggle under reduced motion.
2. **Hero type**: one SplitText line-masked reveal, once per session, ≤ 1.3 s.
3. **Hardware hall**: Three.js (lazy), drag to rotate with inertia, 6°/s idle turn, carousel, AVIF-sprite fallback, procedural placeholder meshes until GLBs exist.
4. **Page transitions**: `--oxblood` panel wipe between routes; shared-element morph from project card to case study.
5. **Scroll moments (exactly three)**: case-cover clip wipe (CSS `view()` timeline), left-gutter signal trace (DrawSVG + ScrollTrigger, desktop, `--rule-strong` per the red rule), Lab telemetry line (draws once; real CSV only, so hidden in production until it exists).
6. **Micro**: button clip-wipe fill + 0.98 press; drawn link underline. Nothing else hovers.

Rules: kill and re-init on `astro:before-swap` / `astro:page-load`; `prefers-reduced-motion` resolves everything to its final state; no content lives only inside a canvas. Easing `--ease-out: cubic-bezier(.16,1,.3,1)`, `--ease-in: cubic-bezier(.7,0,.84,0)`.

## 5. Page blueprints
**Home**: nav (wordmark; Projects, Lab, About; "Get in touch"), hero (copy left, lens right; lens full-bleed under the headline on mobile), selected work (Saarthi large, SETU small), hardware hall (full-bleed oxblood field), lab preview (gated, see §2), final CTA field.

**Engineering case study**: oxblood header (title, summary, status, year, role, specs in mono) → cover → Objective → Architecture (inline diagram, HTML labels) → Constraints → Hardware/firmware → Bench setup → Measurements → Failures & iterations → Status → Links (public only) → prev/next → final CTA. Empty sections are TODO blocks in dev and absent in production.

**Lab entry**: oxblood header (status, date, discipline) → artifact image → body → final CTA.

**About**: photo placeholder, three short paragraphs (who I am; why hardware and software together; what I'm building toward), roles, résumé link. No skill logos.

**Contact**
- Fields: Name, Email, Reason (Internship / Research collaboration / Hardware project / Other), Message. Honeypot. `?reason=` prefills the reason.
- Email subject "New message — {name} ({reason})"; plain-text and HTML bodies, one field per line, then `Message:`; all input escaped.
- Recipient `CONTACT_TO_EMAIL` if set, else `hello@vedantsomani.tech`. Sender `Vedant Somani <hello@vedantsomani.tech>`; the shared Resend test domain is never used in production.
- Success: "Sent. I'll reply by email."

## 6. Content (verified facts only)
**Saarthi (H7-Pro)**: engineering, flagship. Flight-controller firmware on STM32H753. Sensors: dual ICM-42688-P IMUs, DPS310 + BMP390 barometers, MS4525DO airspeed. Mahony filter, fusion benchmark lab, frozen HAL/math contracts. Status: Prototype. Needs: role, year, benchmark CSV, top-down board photo, KiCad plots, GLB model, repo visibility decision.

**PRAHARI**: engineering, restricted. Formally verified, automaton-shielded RL navigation for GPS-denied flight: PPO/SAC over belief state (Isaac Lab), LTL→Büchi shield synthesis, Mealy mission controller. Targets Saarthi on F450; PMW3901 optical flow, VL53L0X rangefinder. Status: TODO(vedant).

**VAJRA**: engineering, restricted. Post-quantum mesh protocol: ML-KEM-768 + X25519 hybrid KEM, ML-DSA-65, ChaCha20-Poly1305. ProVerif models; Rust implementation. Status: Prototype.

**SKYNET / SETU**: lab entry. Heterogeneous autonomous swarm; dual-brain pattern (real-time FC + Linux SBC); SETU airframe (F450-class). Needs: status, third spec, GLB of the frame, photos.

**Saarthi fusion benchmark**: lab entry. Needs: status, date, one-line result, CSV.

**About**: B.Tech CSE, Bennett University (2024–28). Head of Research, Technotix BU and BC3. Core member, BURS. Needs: portrait/workspace photo, résumé PDF, confirmation of the three paragraphs.

Restricted projects (PRAHARI, VAJRA, SKYNET): architecture and results only. No control laws, protocol internals, key handling, or repo links.

## 7. SEO & measurement
- Per-page title (≤ 60 chars), description (≤ 155), canonical on `https://vedantsomani.tech` (no `.html`, no trailing slash). OG images generated at build with Satori (`scripts/og.mjs`): tokens + wordmark.
- `sitemap-index.xml`, `robots.txt`. JSON-LD: `Person` on /about, `CreativeWork` on project pages. No `Service`, `Offer`, reviews, or ratings.
- **Pre-launch**: `PRE_LAUNCH = true` in `src/worker.ts`, so production sends `X-Robots-Tag: noindex, nofollow`. Local audits override it with `npm run preview:audit` (`wrangler dev --var PRE_LAUNCH:false`).
- Security headers in `public/_headers` and on every Worker response; CSP allows `static.cloudflareinsights.com` (script) and `cloudflareinsights.com` (reports).
- Analytics: Cloudflare Web Analytics beacon, gated on `PUBLIC_CF_BEACON_TOKEN`. Custom events through `track()` (a no-op until a backend is chosen): `hero_see_work`, `hero_get_in_touch`, `hero_lens_used`, `project_open`, `hall_object_rotate`, `contact_open`, `form_start`, `lead_submit`, `email_click`, `resume_download`, `github_out`.

## 8. Phases
All phases are complete as of `FINAL_GOAL.md`. The phase files (`01`–`04`) are kept as historical records. Launch steps are at the end of `REPORT.md`.
