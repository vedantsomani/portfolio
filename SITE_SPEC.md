# SITE_SPEC.md — Vedant Somani: Engineering Lab × Freelance Studio

## 1. Positioning
One brand, two proof systems. The homepage sells to clients first; depth lives in /projects and /lab.
Test for every page: understandable in 10 s, credible in 30 s, contactable in 60 s.

- Headline: "Websites and apps, built by an engineer who also writes flight-controller firmware."
- Supporting: "I design, build, and deploy business websites and web apps end to end — from Greater Noida, for clients anywhere."
- CTAs: "Start a project" (primary) · "See the lab" (secondary)
- Availability: "Taking select freelance projects" — TODO(vedant): confirm

Audience priority: (1) local/SMB owner, (2) startup founder, (3) recruiter/tech lead, (4) engineering peer.

## 2. Information architecture
```
/                    Home
/projects            Index — filter: All / Client work / Engineering
/projects/[slug]     Case study (client or engineering template)
/services            Offers, pricing, process, FAQ
/lab                 Build log + hardware hall
/lab/[slug]          Experiment entry
/about               Bio, workspace photo, résumé
/contact             Form + email
/resume.pdf
404                  Custom, with links to Projects and Contact
```

## 3. Design system
| Token | Value | Use |
|---|---|---|
| `--bg` | `#14100E` | Canvas |
| `--surface` | derive: same hue, ~4% lighter | Panels |
| `--ink` | derive warm off-white, ≥ 12:1 on `--bg` | Primary text |
| `--ink-2` | derive, ≥ 4.5:1 on `--bg` | Secondary text |
| `--rule` | derive, low contrast | Structural lines (sparingly) |
| `--oxblood` | `#5A1E14` | Brand fields |
| `--oxblood-hi` | derive lighter oxblood, ≥ 4.5:1 on `--bg` | Links, focus rings, PCB traces |

**Oxblood rules (Lando principle: owned color, used boldly)**
- Oxblood comes from a real object: Saarthi's red solder mask (TODO(vedant): next PCB revision) and the X-ray PCB render.
- Use it in large fields: the full-bleed contact section, case-study headers, page-transition panels, and the primary button fill.
- Never on small text (`#5A1E14` fails contrast). Small accents use `--oxblood-hi`.
- Put the contrast ratios for every pair in a comment in `tokens.css`.

**Type**
- Archivo variable. Display uses expanded `wdth` (~112–125) with heavy weight and tight tracking; body uses `wdth` 100, 17–18 px, measure ≤ 70ch.
- IBM Plex Mono for real data only.
- Modular scale (propose one). Sentence case everywhere.

**Surface & imagery**
- No gradients, no shadows. Depth comes from photography, layering, and surface steps; rules are secondary.
- Imagery: real photos (bench, boards, drones, one consistent lighting setup) > real CAD/3D > diagrams > screen recordings. Never stock or AI images.
- Wordmark: "VEDANT" drawn with PCB-trace geometry (45° corners, pad terminals). TODO(vedant): final SVG. Agent makes a placeholder.
- Grid: 12 columns, 1280 max width, fluid to 320 px.

## 4. Motion system (summary — full spec in `03_PHASE3_MOTION.md`)
1. **Hero X-ray lens** (signature): a photo of Saarthi; the cursor lens reveals the aligned KiCad copper layout. OGL shader with velocity-reactive radius, decaying trail, and noise edge. CSS mask fallback, scripted pass on mobile, toggle under reduced motion.
2. **Hero type:** one line-masked SplitText reveal, once per session, ≤ 1.3 s total.
3. **Hardware hall:** real GLB models (Saarthi PCB, SETU/F450) in a drag-to-rotate carousel with specs in mono.
4. **Page transitions:** oxblood panel wipe between main routes; shared-element image morph into case studies.
5. **Scroll moments (only three):** case-cover clip wipes, the left-gutter signal trace, the Lab telemetry line.
6. **Micro:** button clip-wipe fill, drawn link underlines. Nothing else hovers.

Easing: `--ease-out: cubic-bezier(.16,1,.3,1)`, `--ease-in: cubic-bezier(.7,0,.84,0)`. Durations: 150 / 250 / 400 / 700 / 1200 ms only.

## 5. Page blueprints

### Home
1. Nav: wordmark; Projects, Lab, Services, About; "Start a project" button. Transparent → `--bg` after 40 px scroll. No glass blur.
2. Hero: copy on the left 5 columns, X-ray lens on the right 7 (full-bleed on mobile, below the copy).
3. Selected work: one full-width client case + an asymmetric pair (Saarthi large, one engineering card small).
4. Hardware hall strip: 2 objects, with a link to /lab.
5. Services: 3 offers with "from" prices + a narrow "Connected prototypes" band.
6. Lab preview: 3 entries with status.
7. Process: Scope → Prototype → Build → Test → Launch (a real sequence, so numbering is allowed).
8. Final CTA: full-bleed oxblood field, "Have something worth building?", button, email, GitHub, LinkedIn.

### Case study — client
Problem → Constraints → Approach → Solution (screens/video) → Implementation → Outcome (verified only) → Next improvements → CTA "Build something similar".

### Case study — engineering
Objective → Architecture diagram → Constraints → Hardware/firmware → Bench setup → Measurements → Failures & iterations → Status → Links (public only).

### Services
| Package | Price | Scope | Target |
|---|---|---|---|
| Launch | from ₹15,000 | 1–3 pages, custom responsive UI, enquiry/WhatsApp, analytics, basic SEO, deploy | ~1 week |
| Business | ₹30,000–45,000 | 5–7 pages, CMS/Git content, forms, maps/booking hooks, technical SEO | 2–3 weeks |
| Web app / MVP | ₹60,000–1,20,000 | Auth, database, dashboard/admin, APIs, deploy | 3–6 weeks |
| Care | ₹3,000–8,000/month | Updates, small changes, monitoring | Ongoing |
| Connected prototypes | Scoped individually | Software + embedded | — |

- "Mobile MVP" stays behind a feature flag until a shipped mobile case exists.
- Payment: 50/50 for small sites; 40/30/30 for larger projects.
- Exclusions: domains, paid APIs, third-party subscriptions, app-store fees.
- FAQ: TODO(vedant): 5 real questions.

### Contact
- Fields: name, email, company/site (optional), project type, budget (<₹20k / ₹20–50k / ₹50k–1L / ₹1L+ / Not sure), description. Honeypot. No phone field.
- Microcopy: "No sales call needed for a rough scope." "Half-built product? Send what exists."
- Success: "Sent. I'll reply within 2 working days." TODO(vedant): confirm.

### Lab
Status per entry: Concept / Prototype / Validated / Archived. Each entry has status, date, discipline, one real artifact image, and a one-line hypothesis/result. The hardware hall sits at the top.

## 6. Content (verified facts only)

**Client case #1** — TODO(vedant). Candidate: Bennett University IoT & Robotics Club website redesign (Next.js). Needs: scope, your role, screens, outcome. No Services page ships without at least one client case.

**Saarthi (H7-Pro)** — engineering, flagship. Flight-controller firmware on STM32H753. Sensors: dual ICM-42688-P IMUs, DPS310 + BMP390 barometers, MS4525DO airspeed. Mahony filter, fusion benchmark lab, frozen HAL/math contracts. Status: Prototype. Needs: benchmark CSV, top-down board photo, KiCad plots, GLB model, repo visibility decision.

**PRAHARI** — engineering, restricted. Formally verified, automaton-shielded RL navigation for GPS-denied flight: PPO/SAC over belief state (Isaac Lab), LTL→Büchi shield synthesis, Mealy mission controller. Targets Saarthi on F450; PMW3901 optical flow, VL53L0X rangefinder. Status: TODO(vedant).

**VAJRA** — engineering, restricted. Post-quantum mesh protocol: ML-KEM-768 + X25519 hybrid KEM, ML-DSA-65, ChaCha20-Poly1305. ProVerif models; Rust implementation. Status: Prototype.

**SKYNET / SETU** — Lab entry. Heterogeneous autonomous swarm; dual-brain pattern (real-time FC + Linux SBC); SETU airframe. Needs: GLB of the F450/SETU frame, photos.

**About** — B.Tech CSE, Bennett University (2024–28). Head of Research, Technotix BU and BC3. Core member, BURS. Needs: portrait/workspace photo, résumé PDF.

## 7. SEO & measurement
- Per-page title, description, canonical. OG images generated at build with Satori using the tokens and wordmark.
- `sitemap.xml`, `robots.txt`. JSON-LD `Person` (/about) and `Service` (/services) only for visible content.
- Targets: /services → "freelance web developer India"; /services#websites → "business website developer India".
- Events: `hero_start_project`, `hero_see_lab`, `hero_lens_used`, `project_open`, `hall_object_rotate`, `service_view`, `contact_open`, `form_start`, `lead_submit`, `email_click`, `whatsapp_click`, `resume_download`, `github_out`.

## 8. Phases
- **P0** Design plan → approval (`01_PHASE0_PHASE1.md`)
- **P1** Foundation: scaffold, tokens, layout, Home (static), Services, Contact (`01_PHASE0_PHASE1.md`)
- **P2** Content system, templates, Projects, Lab, About (`02_PHASE2_CONTENT.md`)
- **P3** Signature motion (`03_PHASE3_MOTION.md`)
- **P4** SEO, analytics, QA, launch (`04_PHASE4_LAUNCH.md`)