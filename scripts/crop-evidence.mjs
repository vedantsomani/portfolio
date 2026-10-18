// Evidence crops (SITE_SPEC §5, "The Archive"): cuts the presentation crops the home and /projects
// compositions use out of real source files. Nothing is redrawn, recoloured, or upscaled: every
// output pixel is a source pixel. Re-run after replacing a source:
//   node scripts/crop-evidence.mjs
// Saarthi: the KiCad render and the copper plot share one 2400 × 1600 frame, aligned through the
//   mounting holes by scripts/kicad-hero.mjs, so the same square cut of both stays aligned. The cut
//   is mirrored in src/data/evidence.ts (SAARTHI_CUT), which maps part positions onto it.
// TESSERA: cells of the held-out results grid (tessera-grid.jpg): 6 columns × 5 rows of 256 px
//   panels starting at x 310; rows at y 38, 332, 626, 920, 1214. A 3 px inset drops the panel edges.
import sharp from 'sharp';
import { mkdirSync } from 'node:fs';

const OUT = 'src/assets/work/derived';
mkdirSync(OUT, { recursive: true });

const SAARTHI = { left: 930, top: 300, width: 1000, height: 1000 };
await sharp('src/assets/work/saarthi-hero.jpg')
  .extract(SAARTHI)
  .jpeg({ quality: 92 })
  .toFile(`${OUT}/saarthi-render-sq.jpg`);
await sharp('src/assets/work/saarthi-xray.jpg')
  .extract(SAARTHI)
  .jpeg({ quality: 92 })
  .toFile(`${OUT}/saarthi-plot-sq.jpg`);

const ROWS = { urban: 38, forest: 332, water: 626, desert: 920, agriculture: 1214 };
const COLS = { thermal: 0, baseline: 1, tessera: 2, truth: 3, error: 4, risk: 5 };
const INSET = 3;
for (const [scene, top] of Object.entries(ROWS)) {
  for (const col of ['thermal', 'tessera', 'truth', 'risk']) {
    await sharp('src/assets/work/tessera-grid.jpg')
      .extract({
        left: 310 + 256 * COLS[col] + INSET,
        top: top + INSET,
        width: 256 - 2 * INSET,
        height: 256 - 2 * INSET,
      })
      .png()
      .toFile(`${OUT}/tessera-${scene}-${col}.png`);
  }
}
console.log('evidence crops written to', OUT);
