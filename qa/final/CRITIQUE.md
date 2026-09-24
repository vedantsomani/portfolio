# Self-critique: final build vs. the Lando Norris reference and the AGENTS.md anti-AI rules

Screenshots: `qa/final/<route>-<375|768|1440>.png` (27 files, production build under `wrangler dev`). The captures are full-page, so they pin two things that have no single scroll position: the scroll-linked cover wipe shows its end state, and the fixed nav sits at the top.

## Against the reference (landonorris.com: take the craft, not the layout)
| Craft element | Here | Verdict |
|---|---|---|
| Cursor mask reveal as the signature | X-ray lens on the hero: OGL, velocity radius, decaying trail, noise edge, rim; CSS mask fallback; touch pass; reduced-motion toggle | Present. It only fully pays off with the real photo and KiCad plot: over two placeholders it reads as "the same pattern, recoloured". |
| Objects the viewer can inspect | Hardware hall: Three.js, drag with inertia, idle turn, carousel, sprite fallback | Present. The meshes are procedural placeholders (proportions only, no invented detail) until the GLBs exist. |
| Sharp transitions | Oxblood panel wipe (250 ms in / 300 ms out); card → case-study cover morph | Present and short; no float. |
| Big owned colour | Oxblood only as full-bleed fields (hall, final CTA, case headers, contact header, wipe) | Matches the red usage rule. |

## Anti-AI rules (reject on sight)
- Fade-and-slide-up on every section: **none**. The only entrance is the one headline reveal, by line, once per session.
- Word/character text reveals: **none** (lines only, hero only).
- Smooth-scroll libraries or scroll hijacking: **none**. The wheel never zooms the hall.
- Site-wide custom cursor, particles, fake terminal, glitch, magnetic buttons, tilt cards: **none**. The lens ring exists only over the hero photo; the native cursor stays.
- ALL-CAPS eyebrows, `A · B · C` meta strings, `→` on buttons: **none**.
- Identical rounded cards, one radius, gradients, drop shadows: **none**. Corners are square; depth comes from surface steps. (The link underline is drawn with a single-colour `linear-gradient` background image; nothing visible is a gradient.)
- Accenting one word of a headline: **none**.
- 01/02/03 numbering: **none**. The hall's `1 / 2` is a real carousel position.
- Skill-logo walls, counters, tech-tag filters: **none**. The projects page has no filter because production has one kind.
- Monospace outside real data: **none**. Mono is used for part numbers, specs, status, dates, and the carousel count.
- Red: `--oxblood-hi` only on buttons, focus rings, error text, link hover, and inside imagery (the X-ray copper and lens rim, the placeholder board's traces). The signal trace uses `--rule-strong` rather than oxblood, so the rule holds.
- Stock, AI images, device mockups: **none**. Every image is a generated PCB placeholder marked TODO(vedant) in dev.

## Flagged in review, and fixed
1. `/projects` (1440): the PRAHARI/VAJRA pair collapsed into one narrow track. The lead card's `grid-column: 1 / 9` created implicit columns in the one-column list. Fixed (`.projects > .work-card { grid-column: 1 / -1 }`).
2. The page-transition panel showed in full-page captures (a fixed element one viewport down). It is now `visibility: hidden` except while it animates.
3. Case-study prev/next, log titles, and lab-list titles drew underlines across the whole grid cell. Links now size to their text.
4. On `/lab` the hall stage and card were `--bg` on `--bg`, with no edges. They are now `--surface` there (on Home they sit on the oxblood field).
5. `/lab` CLS 0.185: the hall rebuilt its layout when Three.js arrived. The JS layout is now in place from first paint (keyed on `html[data-motion]`, set before paint). CLS is now 0.
6. Home LCP was 2.06 s: stylesheets are now inlined and Home skips the font preload. LCP now measures 1.5–1.99 s.
7. `/projects` heading order (h1 → h3): the index cards are h2.
8. The Saarthi page's CLS went to 0.059 when the font preload was dropped (the expanded display cut has no metric-compatible fallback). The preload is restored on every page but Home, whose headline waits for its reveal anyway.
9. Contact: the form intro said "unless marked optional", but no optional fields are left. It now reads "All fields are required."

## Left as is, on purpose
- The desktop hero leaves space between the headline and the supporting copy; the copy is anchored to the photo's bottom edge. That is the intended composition.
- Lab entries are hidden in production (no status yet), so `/lab` ships only the hall. The telemetry plot is hidden until the real CSV exists (no invented data). Home's lab preview is hidden for the same reason.
- About's three paragraphs are grounded in SITE_SPEC §6, but their wording is marked TODO(vedant) for confirmation.
