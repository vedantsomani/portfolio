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
/                    Home, in film order: cold open → portrait (hero) → machine reveal → Saarthi →
                     ANAV → TESSERA → the lab's door → hardware hall → contact (final CTA) → credits
/briefing            Recruiter briefing (decided 2026-10-16): an identity-card handoff, then a
                     stable one-page summary. Linked from the cold-open gate and the nav.
/projects            The lab (a rendered room holding every record), then the index: case files (evidence on show), smaller records, restricted records (dossiers),
                     then more projects, with a discipline filter (All, Hardware, Autonomy, AI,
                     Security, Software; `?d=` deep-links one). The filter needs JS; without it
                     every project shows.
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
The lab preview left Home on 2026-10-16 (the film's order has no place for it); /lab keeps the log.

## 3. Design system — "The Archive" (decided 2026-10-16)
**Premise.** The site is a film. After the machines, a visitor finds the surviving records of one engineer. Two worlds, two grades: the **human world** (cold, desaturated grey-green: the photos, the story, About) and the **machine world** (blood and signal red: the tear, HUDs, fields, transitions). Every crossing between them is a moment. Only the frame is fiction: every fact on the page stays real (§6), and nothing implies that Vedant's defence-adjacent work is the thing that ended the world.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#090A09` | Canvas (human world) |
| `--surface` | `#111311` | Panels |
| `--ink` | `#E7E9E4` (16.2:1 on bg) | Primary text |
| `--ink-2` | `#979D95` (7.2:1 on bg) | Secondary text, status marks |
| `--rule` / `--rule-strong` | `#222621` / `#5D655B` | Structural lines / input borders, the signal trace |
| `--oxblood` | `#3D0507` | Blood: large fields, the page-cut panel |
| `--oxblood-hi` | `#FF2E3B` (5.39:1 on bg, 4.66:1 on blood) | Machine red: buttons, focus, HUD, the tear, link hover |

- Red belongs to the machine world: buttons, focus rings, error text, link hover, HUD readouts, the tear, the cold open's traces, and blood fields. Body copy and status marks stay `--ink` / `--ink-2`.
- Contrast ratios for every pair are in `src/styles/tokens.css`.
- **Film layer** (`src/styles/film.css`): grain and vignette over every page; blood fields carry scan lines and a slow pulse; glow (`--glow`) only on machine-world elements.

**Type**: Archivo variable, subset to the characters the site sets (`scripts/subset-fonts.py`, wght 300–800, wdth 100–125; `scripts/qa/glyphs.mjs` flags any character outside it). Display `wdth` 125 / 800; cold-open and chapter cards `wdth` 125 / 300, uppercase, wide tracking that opens slowly (the Last of Us title cards). Body `wdth` 100, 17–18 px, measure ≤ 70ch. IBM Plex Mono for real data and for HUD readouts, whose numbers are always live (pointer position, the visitor's clock, measured frame rate), never invented.

**Imagery**: real photos > real CAD/3D > diagrams. Never stock, never AI-generated, never a fabricated image of Vedant. Machine-vision looks are computed from the real photo in a shader. Hero portrait: `src/assets/portrait/vedant.jpg`, Vedant's own photo. **Exception (Vedant, 2026-10-17):** its background and lighting were changed with an AI image editor; the face, expression, and clothes are the original photo. The alt text and the footer credits say so, and no other image of Vedant may be AI-edited without a new decision here. (Without the file, the desk photo stands in); its crop is one focal point (`hero.focus`) shared by the CSS and the shader. A literal metallic face (endoskeleton) is out of scope: the shader can only reinterpret the photo, so it would need a separately commissioned VFX asset and a new decision here. Evidence crops (the Saarthi square, the TESSERA cells) are cut from real source files by `scripts/crop-evidence.mjs`, never redrawn. Projects with no published image get no picture, never a stand-in. **Set renders (Vedant, 2026-10-17):** the lab on /projects and the briefing's handoff are fictional sets built in Blender (`blender/lab.py`, `blender/briefing.py`: modelled in code, no downloaded assets, Cycles) and every one says so on the page ("Set rendered in Blender", "Rendered sequence"). Inside a set, only real material carries information: screens, prints, and labels show the real project files, record IDs and titles, and the card shows the page's own card. No project hardware is modelled (the Saarthi board exists in the lab only on the laptop's screen, because it has not been fabricated), restricted records are closed cases, and the hand in the briefing is a purpose-made gloved hand, nobody's likeness. Grain sits behind the content (type and diagrams stay crisp); photographs carry their own. Grid: 12 columns, 1280 max, fluid to 320.

## 4. Motion system
0. **Cold open** (`IntroCredits.astro`, `src/scripts/intro.ts`): home, first visit per session, motion allowed, JS on. A title gate ("The Archive"; enter with sound / in silence) while red veins creep in; then credits (Vedant Somani presents → Flight hardware → Secure comms → Space data → built from the silicon up → the name), each fading in as its tracking opens, a sub boom per card; on the silicon card the veins dim and straight copper traces route in from the edges (the organic becomes the machine); a red flash and static cut to the hero. Skip button and Escape always work; the rest of the page is inert meanwhile; a CSS failsafe removes the overlay after 4 s if the script never takes over.
1. **The targeting lock** (hero, OGL; replaced the tear on 2026-10-17). The photo owns the right of the frame at full strength (desktop) or leads full-bleed (phones), never dimmed by an overlay; the headline sits beside the subject. A targeting box (corner brackets) follows the pointer with a slight lag and opens red machine vision inside it (Sobel edges, night-vision gain, scan lines, rolling bar, chromatic split, grain, flicker, the eye glow at `hero.eye`). When the box settles it locks (the brackets snap, a tick cue) and a scan line runs down it, reading what is beneath the skin: wherever the photo is skin (warm and lit: the face, the neck), steel plates fixed to the photo, their relief taken from the photo's own shading so the face keeps its shape and stays recognisable, lit by a drifting light, with red light in the seams between them and an aperture turning at the measured eye; hair, eyes, teeth, shirt and hall stay machine vision. When the box moves on, the window shuts line by line like an interlaced display, the closing rows glowing red. The readout under the box says Tracking or Locked with the box's position in photo pixels; the corner HUD shows subject, clock, frame rate; nothing else is a number. Touch: a tap locks where it lands and lets go after a few seconds; a horizontal drag moves the box. Once per session, as the photo comes up after the cold open, the system makes one pass by itself (acquires the face, locks, reads, lets go). CSS fallback: the same photo through a red filter inside the box. A **Machine vision** button beside the CTAs is the same control for keyboard, touch, and mouse: with the shader it opens the whole photo from the focal point along an irregular front and closes it slowly behind a red trace; otherwise it cuts to the CSS layer (the only treatment under reduced motion). Heartbeat cue when the whole photo opens. **Machine reveal**: scrolling the hero away opens the same front across the photo (closing it on the way back), the crossing into the records.
2. **Hero type**: one SplitText line-masked reveal, once per session, ≤ 1.3 s; after the cold open when one plays.
3. **Hardware hall**: Three.js (lazy), drag to rotate with inertia, 6°/s idle turn. Saarthi loads `public/models/saarthi.glb`. (Planned: red wireframe hologram with a scan plane.)
4. **Page cuts**: the blood panel (scan lines, hot leading edge, static cue) wipes between routes; shared-element morph from project card to case study.
5. **Scroll moments** (`src/styles/scroll.css`, CSS view timelines): *rise* (text out of a mask), *scan* (a photo opens behind a red scan line, red-graded, settling into the human grade by the time it has entered; restrained, never while it is read), *draw*, *drift*. Signature evidence moments: the Saarthi plate (the copper plot replaces the KiCad render behind a descending scan line and rests at a half split, labels on the KiCad part positions), the TESSERA strip read in pipeline order. Lab telemetry line (real CSV only).
5b. **Records**: the cover crosses from the machine's red grade into the human grade behind a scan line (2.2 s, once, on arrival); the title card's tracking opens; the file card fills field by field. On scroll: chapter titles rise and their rule draws; photographs are scanned in; schematics draw stage by stage, each trace running down into the next stage; readout rows rise; Saarthi's board lights system by system as its steps cross the middle of the screen (an IntersectionObserver; without JS every group stays lit). The next record waits in red until hovered or focused.
5a. **Identity card** (/briefing; expanded 2026-10-17): a rendered handoff film (`BriefingHandoff.astro`, 3.5 s, first visit of a session): (1) low across a lamp-lit steel desk, a gloved hand slides the card into the light and lets go; (2) the camera reads along the card, photo to name to headline, in shallow focus; (3) it rises until it looks straight down on the card; at that last frame the page's own card is laid exactly over the rendered one and moves into its place while the film fades, and the page is still from then on. Skip and Escape always work; a film that has not started within 2.5 s is dropped. Without the film, reduced motion, or no JS: the card's 1.2 s handoff (slides up, rotates flat, settles) or simply in place.
10. **The lab** (/projects, decided 2026-10-17): Cycles renders, no real-time 3D. One 16:9 composition serves every screen; on tall screens it keeps its full height and pans sideways under a swipe (a native horizontal scroll, opening on the bench before the first paint). First visit of a session: the camera walks in from the corridor through the doorway to the bench (rendered frames on a canvas, ~2.8 s, played as they arrive, holding if the next frame is not in yet; any input or Skip ends it; a stall of 4 s skips to the room). Hover, focus, or a first tap aims a pool of light at a record and names it (ID, title, status); the others step back. Choosing one pushes the camera in (the room scales towards it while its rendered close-up comes up, ~0.7 s), then the record opens. Back from a record, the camera pulls out of that record's close-up and focus lands on it. Arrow keys move between records. Reduced motion or no JS: the still room, its links in place.
6. **Reveals**: below-the-fold content fades in once, 12 px up, 400 ms. Never the hero, a page header, or the LCP element. CSS failsafe after 2.5 s.
7. **Micro**: button clip-wipe fill + 0.98 press; drawn link underline; project-card hover (cover ≤ 8 px, frame line, arrow nudge).
8. **Planned** (phase order): push-in through the eye into a scroll-driven flight over the Saarthi board; case files and redacted dossiers (PRAHARI, VAJRA, SKYNET: architecture and results only, the redaction is the drama); hologram hall; contact as a transmission; end credits in the footer; film timecode and chapter menu; trailer mode; vertical-trailer phone layout.
9. **Sound** (`src/scripts/sound.ts`): synthesised with Web Audio, no files. Off by default, remembered, toggle in the nav. Drone, heartbeat (tear), boom (credits), static (cuts), tick (HUD).

Rules: kill and re-init on `astro:before-swap` / `astro:page-load`; `prefers-reduced-motion` resolves everything to its final state and skips the cold open; no content lives only inside a canvas; the site works with JS off. Easing `--ease-out: cubic-bezier(.16,1,.3,1)`, `--ease-in: cubic-bezier(.7,0,.84,0)`.

## 5. Page blueprints
**Home**: nav (wordmark; Projects, Lab, About, Briefing; "Get in touch"), hero (portrait right, headline beside it; photo first on phones), then three records, each an evidence composition: **Saarthi** (the plate: KiCad render over its aligned copper plot, labelled on verified part positions, with a parts manifest), **ANAV** (an evidence board of Vedant's build photos, one bracket on the vehicle, captions from the case study), **TESSERA** (one held-out test scene at a time: ST_B10 thermal input → TESSERA RGB → TESSERA risk, ground truth for comparison; a no-JS radio picker over the five scenes, labels exactly as the results grid prints them). Then **the lab's door** (`LabDoor.astro`): the rendered doorway, full bleed, "Every record is in the lab", the whole frame one link to /projects, which opens on the same frame and walks in, so the two pages are one shot. Then the hardware hall (oxblood field), the final CTA, and the footer credits.

**Projects** opens in **the lab** (`LabRoom.astro`, decided 2026-10-17): an abandoned engineering laboratory, full-height, rendered in Cycles (16:9; tall screens pan across it). A steel workbench under a hanging lamp holds the centrepiece, Saarthi, on a laptop whose screen shows the board file's two real images side by side (the KiCad render and the copper plot); behind it, open racks stand against tall broken windows, so cold daylight and ivy show through the shelves: an evidence rack (TESSERA's results grid as a pinned print, ANAV's airframe photo framed, SMRITI's screenshot on a tablet), an archive rack (Dhwani-Kavach, PitSense, the IoT club website as labelled archive boxes), and a caged rack under the room's only red light, where VAJRA, SKYNET and PRAHARI sit as sealed cases. Haze, a breached ceiling with vines, dead trees beyond the glass; every record has its own small pool of light. Every record is an HTML link laid over its object at the position Blender measured (`src/data/lab-set.json`), named on hover, focus or tap; the page's h1 ("Projects") and a line to the index sit over the room, and the room says it is a rendered set. Then **the index**, the direct route to everything: a short header with the discipline filter → case files (Saarthi, TESSERA, ANAV, SMRITI: evidence visible at every width, title, status and year, summary, up to two results) → smaller records (no published image yet: text only) → restricted records (VAJRA, SKYNET, PRAHARI as dossiers: status, permitted architecture, results, and a line naming what is not published; no images) → more projects → final CTA. Routine page headers (Projects, Lab, About, Contact, 404) are short; record headers with a cover stay under 80% of the viewport.

**Recruiter briefing** (`/briefing`): one page, readable in a minute, built from the same data as the rest of the site (`src/data/site.ts`, the content collections). An identity card (photo, name, programme, focus, location, email) is handed over, then: summary line; education; selected work (Saarthi, TESSERA, ANAV, VAJRA, SKYNET: status, one line, Vedant's contribution where recorded, the key result, link to the record); roles and recognition; contact (email, GitHub, LinkedIn) and the résumé link once `public/resume.pdf` exists. No film effects after the card. Reachable from the cold-open gate ("Recruiter briefing", which skips the film) and the nav.

**Records** (decided 2026-10-17): every case study and lab entry is a recovered record in the archive, read by the machine. Two layers on one page: the human evidence (photos, Vedant's words, the cold grade, quiet type) and the machine's reading of it (red mono: exhibit numbers, evidence classes, sources). The machine layer is the honesty rule made visible (a label names only what the project's own files show: render, simulation, synthetic, not yet measured). Each record has one ID on every page: case studies R-01… in collection order, lab entries L-01… (`recordIds()` in `src/lib/content.ts`).
- **Retrieval** (`RecordHead.astro`): the archive path (Archive / R-01), a title card set like the cold open's credits ("Record 01", tracking opening) and the title; the cover is exhibit 00, labelled with its evidence class (`coverKind`: "KiCad render, not a photograph", "Photograph"…), and arrives in the machine's red grade, crossing into the human grade behind a scan line. A record with no image gets a sealed field with its ID, hollow and huge, never a stand-in picture. Then the file card: the status stamped first, then year, role, built-on credit, specs in mono.
- **Restricted** (PRAHARI, VAJRA, SKYNET): a classification band opens the record ("Restricted — architecture and results only." and what that excludes), and the end of the record names what stays sealed. No fake redaction of invented text.
- **Briefing**: problem, my part, what exists today, key result, as a four-cell dossier; the key result carries the machine's mark.
- **Chapters** from the MDX (Objective → Architecture → Constraints → Hardware/firmware → Bench setup → Measurements → Failures & iterations), numbered, with an index rail on long records. Every figure is a numbered exhibit labelled with its evidence class (`Figure kind`); architecture diagrams are schematics read top to bottom as a signal chain; measurements are readouts (`Readout.astro`): each value with what it is and its source tag (board file, host simulation, SITL simulation, test suite, acceptance test, bench test, synthetic sample, held-out test set, not yet measured).
- **Saarthi** carries a signature exhibit (`BoardStory.astro`): the board map holds still while the record explains it system by system (flight computer, safety controller, sensors), each group lighting red as its step is read. **TESSERA** carries its pipeline exhibit (`TesseraScenes.astro`): thermal input → output → risk, one held-out scene at a time.
- **End of record** (`RecordEnd.astro`): the status stamped, sealed or public links, "End of record R-01", the next record waiting in the machine's red grade (hover or focus brings it into the human grade), the previous record, and a quiet line to the contact page. Empty sections are TODO blocks in dev and absent in production.

**Inner-page sign-off**: About, Lab, and Projects end on a quiet channel line (`ChannelLine.astro`: a drawn signal trace, one ask, the direct routes); the full blood-field call to action is the home page's contact beat only.

**About** is the subject file, the human centre: no red, no scan lines. The portrait (held still beside the file on desktop, leading on phones), "Subject file", the name, the file fields (programme, based in, works on), then the statement in three short paragraphs (who I am; why hardware and software together; what I'm building toward). Then 01 Roles (with study and programmes) and the résumé link, 02 Log (dated facts only, dates in mono, a spine that draws as it is read), 03 Toolchain grouped by domain, where every tool links to the project that used it. No skill logos, no counts.

**Lab** is the workshop: the hardware hall on its blood field ("The board, in the round"), the telemetry line once a real CSV exists, then the field records as dossiers (status, permitted architecture, result, what stays sealed).

**Not found**: "No record at this address.", with the requested path read from the browser, and routes to the archive, the briefing, contact, and home.

**Contact** is an open channel: the header (email), then a console: what the channel is for (the form's reasons), how replies come (email), the direct lines (email, GitHub, LinkedIn), and the transmission panel holding the form.
- Fields: Name, Email, Reason (Internship / Research collaboration / Hardware project / Other), Message. Honeypot. `?reason=` prefills the reason.
- Email subject "New message — {name} ({reason})"; plain-text and HTML bodies, one field per line, then `Message:`; all input escaped.
- Recipient `CONTACT_TO_EMAIL` if set, else `hello@vedantsomani.tech`. Sender `Vedant Somani <hello@vedantsomani.tech>`; the shared Resend test domain is never used in production.
- Success: "Sent. I'll reply by email."

## 6. Content (verified facts only)
Every fact below is traced to a file in `ASSET_INVENTORY.md` (path and line). **Status labels must match the evidence**: a label names the strongest thing the project's own files show, never a stage it has not reached. The allowed labels and their exact wording live in `src/lib/content.ts`.

**Saarthi plate imagery** (the hero shows Vedant's portrait, or the desk photo until it exists): the KiCad render and the copper plot both come from the Saarthi board file `Saarthi-H7-Pro-v1.kicad_pcb` (SHA-256 `7030b493…4a820b08`, 2026-09-24), aligned through the mounting holes by `scripts/kicad-hero.mjs`; the plate is a square cut of both. The caption says the render is not a photograph. Replace it with a real top-down photo once the board is fabricated.

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
