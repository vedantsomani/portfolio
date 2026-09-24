# ASSETS.md — files the site expects from Vedant

Every slot below currently shows a generated placeholder (a PCB pattern made by `scripts/placeholders.mjs`) or is hidden in production. Nothing here may be stock, AI-generated, or a device mockup.

## How to hand files over
- **Photos:** drop originals into `src/assets/inbox/` (any size, JPG/PNG/HEIC exported to JPG). Each is cropped to its slot's aspect ratio, exported as AVIF + JPG through Astro's image pipeline, and given real alt text. Put one line per file in `src/assets/inbox/README.txt` saying what it shows; that line becomes the alt text.
- **Models:** `public/models/<id>.glb` (`saarthi.glb`, `setu.glb`). The build detects them (`astro.config.mjs` → `__MODELS__`) and the hall loads them instead of the procedural meshes. Then re-run `npm run sprites` for the no-WebGL fallback.
- **Data:** `public/data/fusion-benchmark.csv`. The telemetry plot appears (in production) once it exists.
- **Résumé:** `public/resume.pdf`. The About page links it once it exists.

## Photos and renders

| Slot | Replaces | Size / ratio | Format, budget | What the shot must show |
|---|---|---|---|---|
| Hero photo | `src/assets/placeholders/hero-photo.jpg` | 2400×1600 (3:2); mobile uses a 4:3 centre crop | AVIF ≤ 150 KB desktop source, ≤ 60 KB mobile 4:3 source; JPG fallback | Saarthi H7-Pro top-down on the bench, one consistent diffuse light. **The left third of the frame is dark bench with no board in it** (on desktop the headline overlaps the photo's left edge and must read without a scrim). **All 4 mounting holes visible and unobstructed**: they are the registration points for aligning the X-ray layer. Camera square to the board, no perspective. |
| Hero X-ray | `src/assets/placeholders/hero-xray.jpg` | 2400×1600, pixel-aligned to the hero photo | AVIF ≤ 150 KB | KiCad → Plot → SVG of F.Cu + B.Cu + F.Silkscreen, recoloured (copper `#E25964`, background `#14100E`), rasterised at 2400×1600 and aligned to the photo using the 4 mounting holes. |
| Saarthi cover | `saarthi-cover.jpg` | 1600×1200 (4:3) | AVIF | Saarthi board, top-down or three-quarter, same light as the hero. |
| PRAHARI cover | `prahari-cover.jpg` | 1600×1200 | AVIF | A flight or simulation still that shows no restricted internals. |
| VAJRA cover | `vajra-cover.jpg` | 1600×1200 | AVIF | A diagram or bench image that shows no protocol internals or keys. |
| SETU photo | `skynet-cover.jpg` | 1200×1600 (3:4) | AVIF | The SETU airframe (F450-class), whole frame in view. |
| Fusion benchmark artifact | `fusion-artifact.jpg` | 1600×1000 | AVIF | A plot from the benchmark, or the bench rig running it. |
| About portrait | `about-portrait.jpg` | 1200×1500 (4:5) | AVIF | Vedant at the bench or the workspace, same light family as the hero. |
| Hall posters (no-JS view) | `hall-saarthi.jpg`, `hall-setu.jpg` | 1200×1200 | AVIF | A still render of each GLB, on `#14100E`. |

## 3D models

| File | Source | Budget | Notes |
|---|---|---|---|
| `public/models/saarthi.glb` | KiCad → STEP → Blender → GLB | ≤ 2 MB, Meshopt-compressed | Matte materials; red solder mask if the next revision has it. Origin at the board centre. |
| `public/models/setu.glb` | Fusion 360 → GLB | ≤ 2 MB, Meshopt-compressed | Whole frame; props optional. |

## Data

| File | Format | Notes |
|---|---|---|
| `public/data/fusion-benchmark.csv` | CSV, first two numeric columns plotted as x, y (e.g. `t_ms,roll_deg`); header row allowed | Real Saarthi IMU fusion benchmark output only. |

## Other
- `public/resume.pdf`: current résumé.
- Wordmark: final "VEDANT" SVG in PCB-trace geometry to replace `src/lib/wordmark.ts`.
