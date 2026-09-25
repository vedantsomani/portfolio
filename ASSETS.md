# ASSETS.md — files the site uses and still expects from Vedant

Real files live in `src/assets/work/`, `public/models/` and `public/hall/`. Slots without a real file show a generated placeholder (a PCB pattern from `scripts/placeholders.mjs`) or are hidden in production. Nothing here may be stock, AI-generated, or a device mockup. The sources behind every file are listed in `ASSET_INVENTORY.md`.

## How to hand files over
- **Photos:** drop originals into `src/assets/inbox/` (JPG/PNG; HEIC exported to JPG). Each is cropped to its slot, re-encoded (which strips EXIF and location), and given real alt text. Put one line per file in `src/assets/inbox/README.txt` saying what it shows.
- **Saarthi board art (hero, X-ray, GLB):** always regenerate all three from the **same** `.kicad_pcb`, so the X-ray lens stays aligned and the hall shows the same board:
  1. `node scripts/kicad-hero.mjs <board.kicad_pcb>` renders the board top-down, plots F.Cu + B.Cu + F.Silkscreen, fits the plot to the render through the mounting holes (the run fails above 1 px error), and writes `src/assets/work/saarthi-hero.jpg` and `saarthi-xray.jpg`. Set `KICAD_CLI` if `kicad-cli` isn't on PATH.
  2. `kicad-cli pcb export glb -o saarthi-raw.glb --subst-models --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask <board.kicad_pcb>`, then `npx @gltf-transform/cli optimize saarthi-raw.glb public/models/saarthi.glb --compress meshopt --texture-compress false`.
  3. `npm run sprites` for the no-WebGL fallback.
- **Data:** `public/data/fusion-benchmark.csv`. The telemetry plot appears (in production) once it exists.
- **Résumé:** `public/resume.pdf`. The About page links it once it exists. No phone number in it.

## Images

| Slot | File | Size / ratio | Status | Source / what it must show |
|---|---|---|---|---|
| Hero photo | `src/assets/work/saarthi-hero.jpg` | 2400×1600 (3:2) | **KiCad render** (caption says so) | Board file SHA-256 `7030b493…`, 2026-09-24. Replace with a real top-down photo once fabricated: camera square to the board, all 4 corner holes visible, board within x 1000–1860 of the 2400-px frame (the desktop lens box only shows the frame's middle, and the headline covers up to x ≈ 980), dark bench elsewhere. Then re-fit the X-ray to the photo through the holes |
| Hero X-ray | `src/assets/work/saarthi-xray.jpg` | 2400×1600, pixel-aligned | **Real KiCad plot** | F.Cu (copper `#E25964`), B.Cu at 30 %, F.Silkscreen in `--ink-2`, on `#14100E` |
| Saarthi cover | `src/assets/work/saarthi-cover.jpg` | 1600×1200 | KiCad render (45°) | Replace with a board photo in the hero's light once fabricated |
| Saarthi case figure | `src/assets/work/saarthi-top.jpg` | 1600×1600 | KiCad render (top) | — |
| Hall poster (no-JS) | `src/assets/work/hall-saarthi.jpg` | 1200×1200 | KiCad render | — |
| TESSERA cover + figure | `tessera-cover.jpg` (4:3, padded white), `tessera-grid.jpg` | 1960×1470, 1846×1470 | **Real results** | `isro1/outputs/judge_panels_scaleup/scaleup_judge_comparison_grid.png` |
| SMRITI cover + figures | `smriti-cover.jpg`, `smriti-f2/f3/f7.png`, `smriti-training.png`, `smriti-confusion.png` | 1600×1200 etc. | **Real screenshots and plots** | Phone screenshots with demo personas only; plots from the model trained on synthetic data (captioned) |
| VAJRA cover | placeholder `vajra-cover.jpg` | 1600×1200 | TODO | A diagram or bench image with no protocol internals or keys |
| Dhwani-Kavach cover | placeholder `dhwani-cover.jpg` | 1600×1200 | TODO | Signal-chain plot or bench photo |
| PitSense cover | placeholder `pitsense-cover.jpg` | 1600×1200 | TODO | Dashboard screenshot |
| IoT club site cover | placeholder `iot-cover.jpg` | 1600×1200 | TODO | Screenshot of the site, plus a working live URL |
| SKYNET artifact | placeholder `skynet-cover.jpg` | 1200×1600 (3:4) | TODO | Aircraft photo (SETU only once confirmed) |
| PRAHARI artifact | placeholder `prahari-cover.jpg` | 1600×1200 | TODO | A simulation still with no restricted internals |
| Fusion benchmark artifact | placeholder `fusion-artifact.jpg` | 1600×1000 | TODO | A plot from the real benchmark, or the bench rig running it |
| About portrait | placeholder `about-portrait.jpg` | 1200×1500 (4:5) | TODO | Vedant at the bench or workspace |

## 3D models

| File | Status | Notes |
|---|---|---|
| `public/models/saarthi.glb` | **Real**, 1.29 MB, Meshopt | Exported from the same board file as the hero (23.7 MB raw → 1.29 MB) |
| `public/models/setu.glb` | Not used | SETU is off the site until confirmed |

## Audio
Dhwani-Kavach: none yet. At most 2 short before/after clips, with only Vedant's voice. The synthetic demo pair in the repo is not his voice, so it doesn't qualify.

## Data

| File | Format | Notes |
|---|---|---|
| `public/data/fusion-benchmark.csv` | CSV, first two numeric columns plotted as x, y (e.g. `t_ms,roll_deg`); header row allowed | Real Saarthi IMU fusion benchmark output only. Host-simulation CSVs don't qualify |

## Other
- `public/resume.pdf`: current résumé, clean (no phone number, no template placeholders).
- Wordmark: final "VEDANT" SVG in PCB-trace geometry to replace `src/lib/wordmark.ts`.
