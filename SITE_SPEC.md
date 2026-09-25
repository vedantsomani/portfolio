# SITE_SPEC.md — Vedant Somani: engineering portfolio

Source of truth for content, design, and motion. Updated to `FINAL_GOAL.md` (portfolio only, no freelancing). Where the phase files `01`–`04` disagree with this file, this file wins; they are historical.

## 1. Positioning
A personal engineering portfolio. No freelance offer, pricing, or process.

- Headline: "Flight hardware, secure comms, and space data — built from the silicon up."
- Supporting: "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them."
- CTAs: "See the work" → `/projects` (primary) · "Get in touch" → `/contact` (secondary). The nav button is "Get in touch".
- Final CTA field: "Working on something hard?" + "Get in touch".

Audience: recruiters, research labs, collaborators, and future co-founders and investors for a defence-tech startup.
Test for every page: understandable in 10 s, credible in 30 s, contactable in 60 s.

## 2. Information architecture
```
/                    Home: hero (X-ray lens) → selected work → hardware hall → lab preview → final CTA
/projects            Engineering projects (no filter: one kind in production)
/projects/[slug]     Engineering case study: saarthi, tessera, vajra, smriti, dhwani-kavach,
                     pitsense, iot-club-website
/lab                 Hardware hall + telemetry + build log (entries grouped by status)
/lab/[slug]          Lab entry (only entries with a status are built in production): skynet, prahari
/about               Photo, three paragraphs, roles, résumé link (hidden)
/contact             Form + email
/resume.pdf          Hidden: no link until Vedant supplies a clean PDF (the found ones expose a
                     phone number or template placeholders)
404                  Custom, with links to Projects, Contact, Home
/services            301 → / (retired)
/projects/prahari    301 → /lab/prahari (PRAHARI is a concept, not a project)
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
3. **Hardware hall**: Three.js (lazy), drag to rotate with inertia, 6°/s idle turn, carousel, AVIF-sprite fallback. Saarthi loads `public/models/saarthi.glb`, exported from the same board file as the hero. SETU is out until confirmed, so the hall has one object and hides its carousel controls. Procedural meshes remain for any object without a GLB.
4. **Page transitions**: `--oxblood` panel wipe between routes; shared-element morph from project card to case study.
5. **Scroll moments (exactly three)**: case-cover clip wipe (CSS `view()` timeline), left-gutter signal trace (DrawSVG + ScrollTrigger, desktop, `--rule-strong` per the red rule), Lab telemetry line (draws once; real CSV only, so hidden in production until it exists).
6. **Micro**: button clip-wipe fill + 0.98 press; drawn link underline. Nothing else hovers.

Rules: kill and re-init on `astro:before-swap` / `astro:page-load`; `prefers-reduced-motion` resolves everything to its final state; no content lives only inside a canvas. Easing `--ease-out: cubic-bezier(.16,1,.3,1)`, `--ease-in: cubic-bezier(.7,0,.84,0)`.

## 5. Page blueprints
**Home**: nav (wordmark; Projects, Lab, About; "Get in touch"), hero (copy left, lens right; lens full-bleed under the headline on mobile), selected work (Saarthi large, TESSERA small), hardware hall (full-bleed oxblood field), lab preview (gated, see §2), final CTA field.

**Engineering case study**: oxblood header (title, summary, status, year, role, specs in mono) → cover → Objective → Architecture (inline diagram, HTML labels) → Constraints → Hardware/firmware → Bench setup → Measurements → Failures & iterations → Status → Links (public only) → prev/next → final CTA. Empty sections are TODO blocks in dev and absent in production.

**Lab entry**: oxblood header (status, date, discipline) → artifact image → body → final CTA.

**About**: photo placeholder, three short paragraphs (who I am; why hardware and software together; what I'm building toward), roles, résumé link. No skill logos.

**Contact**
- Fields: Name, Email, Reason (Internship / Research collaboration / Hardware project / Other), Message. Honeypot. `?reason=` prefills the reason.
- Email subject "New message — {name} ({reason})"; plain-text and HTML bodies, one field per line, then `Message:`; all input escaped.
- Recipient `CONTACT_TO_EMAIL` if set, else `hello@vedantsomani.tech`. Sender `Vedant Somani <hello@vedantsomani.tech>`; the shared Resend test domain is never used in production.
- Success: "Sent. I'll reply by email."

## 6. Content (verified facts only)
Every fact below is traced to a file in `ASSET_INVENTORY.md` (path and line). **Status labels must match the evidence**: a label names the strongest thing the project's own files show, never a stage it has not reached. The allowed labels and their exact wording live in `src/lib/content.ts`.

**Hero imagery**: the hero "photo" is a KiCad render and the X-ray is the KiCad copper plot. Both come from the Saarthi board file `Saarthi-H7-Pro-v1.kicad_pcb` (SHA-256 `7030b493…4a820b08`, 2026-09-24), aligned through the mounting holes by `scripts/kicad-hero.mjs`. The caption says "KiCad render". Replace it with a real top-down photo once the board is fabricated.

**Saarthi (H7-Pro)**: engineering, flagship. A dual-MCU flight controller for fixed-wing and glider airframes: an STM32H753ZIT6 flight computer, plus an STM32G431CBU6 safety/output MCU that alone drives the 12 servo outputs. Sensors on the current board: BMI088 + 2× ICM-42688-P IMUs, MS5611 + DPS310 barometers. There is no BMP390, and the MS4525DO airspeed sensor is an off-board module, not on the board. Board: 90 × 90 mm chamfered, 4 layers, 80 × 80 mm M3 + 30.5 mm stack pattern; regulated 5 V from a separate 3S/4S PDB. Status: **"In layout — schematic complete, routing in progress"**. Never "Prototype" or "flight-tested". Year 2026. Role: hardware architecture, KiCad schematic and layout, FlightCore software. FlightCore is a portable C11 core, tested on a host PC only: 72/72 host tests; a 100,000-seed stress campaign on a host model; IMU-only drift about 1.0 m in 10 s at 0.02 m/s² bias. Board checks 2026-09-24: 0 ERC errors; 4 DRC errors (USB-C hole clearance); 386 unrouted. Still needed: a photo of the fabricated board, a real fusion-benchmark CSV, and a repo visibility decision.

**TESSERA**: engineering, flagship. ISRO Bharatiya Antariksh Hackathon 2026, Problem Statement 10 (infrared colourisation and enhancement). Vedant was team leader (team of 4). Landsat ST_B10 thermal in; enhanced IR, colour and a hallucination-risk map out. Inference uses the thermal band only. Deployed model: PSNR 24.835786, hallucination proxy 0.023902, 226.78 ms/tile. Status: Research. Visuals: the held-out results grid.

**VAJRA**: engineering, restricted. "Point-to-point post-quantum secure link, v1.0 (frozen)". ML-KEM-768 + X25519 hybrid KEM, ML-DSA-65, ChaCha20-Poly1305 over UDP. Rust core plus a Python reference; ProVerif models (not yet machine-checked). NIST Category 3, not CNSA 2.0. Rust tests: 16 pass; Python: 53/53. Never "mesh".

**SMRITI**: engineering. A local-first household system (laptop home server, companion app, family-care app) with no cloud. Must carry: "not a medical device". The optional play-pace model came from an SIH 2026 problem and was trained on synthetic play events only. Status: Prototype. Visuals: app screenshots (demo personas only) and the model's plots, labelled synthetic. Repo public.

**Dhwani-Kavach**: engineering, small entry. Smart India Hackathon 2026, SIH26052 (DRDO). Live dual-mic speech enhancement, built on FastEnhancer (ICASSP 2026), credited on the page. ΔPESQ 0.0363 vs offline (target < 0.05, pass); demo PESQ 1.088 → 1.602 on one synthetic sample; latency "not yet measured". Status: Bench-tested. Audio: none until a before/after pair with only Vedant's voice exists (max 2 short clips).

**PitSense**: engineering, small entry. An F1 strategy workbench built on the open-source F1 Race Strategy Engine; its defaults are illustrative. Status: Prototype. Repo public.

**IoT & Robotics Club website**: engineering, small entry. Vedant wrote 40 of 40 commits. Next.js, React Three Fiber, Supabase, GSAP. Status: Built. The Vercel URL returned 404 on 2026-09-25, so there is no live link until a working one exists.

**SKYNET**: lab entry, restricted. A dual-brain aircraft stack: Pixhawk FC + Raspberry Pi companion, with GPS, optical flow and a barometer. Status: **"Simulation-tested"** (ArduPilot SITL, 2026-07-14: a 2 m mission; LAND on companion loss). Not yet run on the real Pixhawk or airframe. **SETU** stays off the site until Vedant confirms the airframe and supplies its photo.

**PRAHARI**: lab entry, restricted, status **Concept**. Design stage, no public artifacts. Formally verified, automaton-shielded RL navigation for GPS-denied flight: PPO/SAC over a belief state in Isaac Lab, an LTL→Büchi shield, and a Mealy mission controller; PMW3901 and VL53L0X sensors; targets Saarthi.

**Saarthi fusion benchmark**: lab entry, hidden until a real IMU CSV exists. The flightcore CSVs are host simulation and do not qualify.

**Not on the site**: Krishi Darpan (left off), the graphene slide (not Vedant's), club photos (none confirmed as Vedant's builds), and any claim about the `AWS` repo (unconfirmed).

**About**: B.Tech CSE, Bennett University (2024–28).
- Head of Research, Technotix BU, the IoT & Robotics Club (since Feb 2026). Coordinated drone, ESP32, and sensor-integration work in a five-member subgroup; two workshops (UAV basics, ESP32 sensor interfacing) for 250+ attendees; mentored 50+ juniors.
- Head of Research, BC3, the Bennett Cloud Computing Club (since Oct 2025). Organised edge-computing and deployment-pipeline workshops.
- Member, BURS, the Bennett Undergraduate Research Society (2024–25).
- Altium Global Scholarship Program 2026: selected.
- Sources: cv (4) p1 (May 2026); cv-2 p1–2 (Aug 2026).
- Needs: a portrait or workspace photo, a clean résumé PDF, and confirmation of the three paragraphs.

**More projects** (the list on /projects; the data and per-entry sources are in `src/data/archive.ts`). Sources: the old portfolio's project list (`Downloads/cv/content.py`), résumés cv (4) and cv-2, LinkedIn project entries (screenshots, 2026-09-25), repo READMEs, and the live sites. Each entry shows its evidence type (live site, public repo, LinkedIn, résumé, local only), so a résumé or LinkedIn claim never reads as a verified measurement.
- CodeSaaS (2026): seven-agent code generator on LangGraph, AWS Bedrock, E2B, Next.js. Live at aws-six-omega.vercel.app; repo `AWS`.
- IRoC-U 2026 indoor quadrotor (Jan–Apr 2026): GPS-denied, PX4 + Jetson Nano + stereo depth + optical flow; flight tests in a 5 m × 5 m arena, with teammates. Repo `irocu-2026` not linked until its README is replaced.
- Krishi Darpan (Oct 2025–): team; Earth Engine advisory, XGBoost crop ranking (15+ crops, 78% on field data), quantized MobileNet under 6 MB (80% on an open benchmark), multilingual; Project Showcase 2.0.
- ANAV (Aug 2024–Apr 2025), now a full case study (`/projects/anav`): Martian-surface landing scenario, ISRO competition; hazard map from camera + IMU, landing-site scoring (flatness, clearance, approach margin), automated approach and touchdown, per LinkedIn. Status "Built": Vedant's photos show the vehicle, tent-hall and outdoor sessions (sent 2026-09-26; crops keep other people's faces out). Repo `Frontend-for-anav` is its ground dashboard. Needs: part numbers, his part, flight logs or video.
- Club drone builds (dates unknown): Vedant's own S550 hexacopter and F450, both Pixhawk + GPS, in Mission Planner (his photos). Needs: dates, whether they flew.
- SKYNET glider: Vedant's wing-printing photo is pending a JPG re-send (the story file did not decode).
- SmartCan (2025): Raspberry Pi waste classification with lid control, per LinkedIn. Repo `Smart-bin` (web app; confirm).
- Cymbot (2024): team mental-health chatbot with assessment quizzes, per LinkedIn.
- Also: GTR 2026 event site (live), line-following robot (Apr–Jun 2023), network analyzer, EduCon, FocusFlow (concept), Campusgram; small experiments Agri, Disaster-One, YouTube ad blocker, Autotyper.
- Not on the site yet (need details or a decision): SKYNET ground robot (restricted), Raven UGV-UAV, CSI WiFi sensing, "lunar ice".

Restricted projects (PRAHARI, VAJRA, SKYNET): architecture and results only. No control laws, protocol internals, key handling, or repo links.

## 7. SEO & measurement
- Per-page title (≤ 60 chars), description (≤ 155), canonical on `https://vedantsomani.tech` (no `.html`, no trailing slash). OG images generated at build with Satori (`scripts/og.mjs`): tokens + wordmark.
- `sitemap-index.xml`, `robots.txt`. JSON-LD: `Person` on /about, `CreativeWork` on project pages. No `Service`, `Offer`, reviews, or ratings.
- **Pre-launch**: `PRE_LAUNCH = true` in `src/worker.ts`, so production sends `X-Robots-Tag: noindex, nofollow`. Local audits override it with `npm run preview:audit` (`wrangler dev --var PRE_LAUNCH:false`).
- Security headers in `public/_headers` and on every Worker response; CSP allows `static.cloudflareinsights.com` (script), `cloudflareinsights.com` (reports), `'wasm-unsafe-eval'` (the hall's Meshopt decoder) and `blob:` in connect-src (textures embedded in the GLB).
- Analytics: Cloudflare Web Analytics beacon, gated on `PUBLIC_CF_BEACON_TOKEN`. Custom events through `track()` (a no-op until a backend is chosen): `hero_see_work`, `hero_get_in_touch`, `hero_lens_used`, `project_open`, `hall_object_rotate`, `contact_open`, `form_start`, `lead_submit`, `email_click`, `resume_download`, `github_out`.

## 8. Phases
All phases are complete as of `FINAL_GOAL.md`. The phase files (`01`–`04`) are kept as historical records. Launch steps are at the end of `REPORT.md`.
