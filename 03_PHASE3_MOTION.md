PHASE 3 — Signature motion. Read `AGENTS.md` and `SITE_SPEC.md` first; both are binding. This prompt is the detailed motion spec behind `SITE_SPEC.md §4`. Phases 1–2 are done: pages and content exist, with no motion yet.

Reference: landonorris.com by OFF+BRAND (Awwwards Site of the Year 2025). Take the craft (the cursor mask reveal, sharp transitions, 3D objects the viewer can inspect), not the layout. My visitors are clients and must reach "Start a project" within 10 seconds.

---

## 1. Hero: "X-ray lens" mask reveal (the signature)

### Concept
Top layer: a real top-down photo of my Saarthi flight controller (STM32H753) on my bench.
Hidden layer: the same board's PCB layout (copper traces, pads, silkscreen) rendered in oxblood on near-black, pixel-aligned to the photo.
The cursor is a lens. Wherever it moves, the photo dissolves and the board's internals show through. Message: "I see inside the product."

### Assets (I provide; create placeholders + an `ASSETS.md` checklist)
- `hero-photo.avif`: 2400×1600, top-down, board centered, ≤ 150 KB. Also a `.jpg` fallback.
- `hero-xray.avif`: KiCad Plot → SVG of F.Cu + B.Cu + F.Silkscreen, recolored (copper `--oxblood-hi`, background `--bg`), rasterized at the same size, aligned to the photo using the 4 mounting holes as registration points.
- Until I provide these, generate placeholders: a flat photo-toned rectangle and a procedural trace pattern. Label both `TODO(vedant)`.

### Implementation
- Library: **OGL** (not Three.js; it's ~10 KB gz) in an Astro island, `client:idle`.
- The photo renders first as a plain `<img fetchpriority="high">`. It is the LCP element. The WebGL canvas mounts over it after idle and cross-fades in (200 ms). No layout shift.
- Fragment shader:
  - Two textures (photo, x-ray). Mix by a mask.
  - Mask = soft circle at the smoothed cursor position. Radius 140 px at rest (desktop), scaled by viewport.
  - **Velocity response:** radius grows with pointer speed (up to 1.6×) and relaxes back over ~600 ms. This is what makes it feel alive rather than a flashlight.
  - **Trail:** render the mask into a ping-pong FBO that decays each frame (factor ~0.92), so fast strokes leave a fading reveal trail.
  - **Edge:** distort the mask edge with 2D simplex noise (amplitude ~12 px, slow time drift). Add a 1–2 px `--oxblood-hi` rim at the mask boundary, like a lens edge.
  - Cursor smoothing: lerp 0.12 per frame toward the pointer (frame-rate independent: `1 - pow(1 - 0.12, dt*60)`).
- DPR capped at 1.5. Pause the RAF loop when the hero is off-screen (IntersectionObserver) or the tab is hidden.
- The native cursor stays visible. Add a small ring that follows the lens only on the hero; no global custom cursor.

### Mobile / touch
- No hover. On first view the lens runs **one scripted pass** (Lissajous path across the board, 2.4 s, then settles center-right at 60% radius).
- Touch-drag moves the lens; page scroll must still work. Use `touch-action: pan-y` and only capture horizontal-dominant drags.
- Low-end guard: if `navigator.hardwareConcurrency <= 4` or the WebGL context fails → CSS fallback.

### CSS fallback (no WebGL, fails, or `saveData`)
Stack both images. Apply `mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), #000 60%, transparent 100%)` to the x-ray layer. Update `--x/--y/--r` from pointer events via `requestAnimationFrame`. Same smoothing, no trail.

### Reduced motion
No lens and no scripted pass. Show the photo with a "Show circuit layout" toggle button that swaps to the x-ray with a 0 ms cut. Fully keyboard operable.

### Accessibility
The canvas is `aria-hidden`. The photo has real alt text: `TODO(vedant)`. All hero copy and CTAs are HTML outside the canvas.

---

## 2. Hero type: one orchestrated load sequence
Headline: "Websites and apps, built by an engineer who also writes flight-controller firmware." (Archivo, expanded width, large.)

- GSAP SplitText by **lines** (not words or characters). Each line is clipped by its own mask and rises from 100% → 0% `yPercent`, 700 ms, `expo.out`, 80 ms stagger.
- Sequence: photo visible at 0 ms → headline lines at 150 ms → supporting line + CTAs fade at 650 ms → lens scripted pass (mobile) or lens activation (desktop) at 900 ms.
- Total ≤ 1.3 s. It runs once per session (`sessionStorage` flag); repeat visits show the final state.
- Everything is visible without JS.

---

## 3. Hardware hall (Lando's "helmets hall of fame", my version)
Section on /lab and a strip on Home: my real hardware as inspectable 3D objects.

- Objects: Saarthi PCB (KiCad → GLB export, or STEP → Blender → GLB), SETU/F450 frame (Fusion 360 → GLB). Placeholders until provided: `TODO(vedant)`.
- Three.js, one shared renderer, `client:visible`. The GLB is loaded only when the section is ≤ 1 viewport away. Meshopt or Draco compressed, ≤ 2 MB each.
- Interaction: drag to rotate (damped, inertia), with an auto-idle slow turn at 6°/s. Scroll wheel does **not** zoom (the page must scroll).
- The object sits on a horizontal carousel. Switching objects: the current one scales 1 → 0.85 and fades while the next rotates in from −30°, 500 ms.
- Beside each object, in HTML: name, one line on what it is, 3 real specs in IBM Plex Mono (e.g. `STM32H753`, `2× ICM-42688-P`, `DPS310 + BMP390`), and a link to the case study.
- Lighting: a single key light + environment map. Matte materials, no bloom, no chrome.
- Fallback: a pre-rendered turntable as a 24-frame AVIF sprite, scrubbed by drag.

---

## 4. Page transitions: sharp, not floaty
- View Transitions (`<ClientRouter />`). Between main routes, a full-viewport `--oxblood` panel wipes in from the bottom (250 ms, `expo.in`), the page swaps, and the panel exits upward (300 ms, `expo.out`).
- Project card → case study: shared-element morph of the cover image (`transition:name`). No wipe on this route pair.
- Reduced motion: instant swap.
- Kill all GSAP ScrollTriggers and WebGL loops on `astro:before-swap`; re-init on `astro:page-load`. Test back/forward.

---

## 5. Scroll moments (only these three)
1. **Selected work:** each case cover is revealed by a horizontal clip-path wipe (`inset(0 100% 0 0)` → `inset(0)`), scrubbed across 30% of the viewport. Uses CSS `animation-timeline: view()`, with GSAP fallback only for Safari if needed.
2. **Signal trace:** one oxblood PCB-style trace in the left gutter, DrawSVG + ScrollTrigger `scrub: 0.5`. It terminates in a pad at each section heading. Desktop only.
3. **Lab telemetry:** real Saarthi IMU fusion benchmark data (`TODO(vedant)`: CSV) plotted as a line that draws once on enter, 1.2 s.

No other scroll animation. No fade-up sections. No smooth-scroll library.

---

## 6. Micro-interactions
- Primary button: background `--oxblood` → `--oxblood-hi` with a 100% → 0% clip wipe on hover (200 ms); `scale(0.98)` on press.
- Links: underline draws left → right on hover (`background-size`), retracts right on leave.
- Nothing else hovers. No magnetic buttons, no tilt cards.

---

## 7. Budgets (merge blockers)
- LCP ≤ 2.0 s (hero `<img>`), INP ≤ 200 ms, CLS ≤ 0.05 on mid-range Android over 4G.
- Initial JS on Home ≤ 90 KB gz (GSAP core + ScrollTrigger + SplitText + OGL island). Three.js and GLBs are lazy.
- The hero shader holds 60 fps on a 2020 mid-range laptop iGPU. Profile in Chrome Performance and report frame times.
- Only transform, opacity, clip-path, mask, and stroke-dashoffset are animated.

---

## 8. Deliver in this order; stop after each for my review
1. Hero mask reveal: CSS fallback first, then the OGL version behind it. Report the fps and bundle size.
2. Hero type sequence.
3. Page transitions.
4. Scroll moments.
5. Hardware hall.

For each: screen-record desktop + mobile (Playwright video), list every `TODO(vedant)` asset, and state what you would cut if it failed a budget.
