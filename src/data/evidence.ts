// Evidence compositions (SITE_SPEC §5): the crops and labels the home records and /projects case
// files use. Every image here is a crop of a real source file, cut by scripts/crop-evidence.mjs;
// every label restates the source (the KiCad file, the results grid's own panel headings, the ANAV
// case study's captions). Nothing is redrawn.
import type { ImageMetadata } from 'astro';
import { HERO_FRAME, PARTS, toFrame, type BoardPart } from './saarthi-board';

import render from '../assets/work/derived/saarthi-render-sq.jpg';
import plot from '../assets/work/derived/saarthi-plot-sq.jpg';

// ---------- Saarthi: one square cut of the aligned render / copper-plot frame ----------
// Must match SAARTHI in scripts/crop-evidence.mjs.
export const SAARTHI_CUT = { left: 930, top: 300, size: 1000 } as const;

export const saarthiPlate = {
  render,
  plot,
  renderAlt:
    'KiCad 3D render of the Saarthi H7-Pro board, top side: a 90 mm square, four-layer board with the STM32H753 at centre-left and twelve servo headers along the bottom edge.',
  plotAlt:
    'The same board as its copper plot from the KiCad file, aligned to the render through the mounting holes.',
  source:
    'KiCad render and copper plot from the board file of 24 September 2026. Not a photograph: the board has not been fabricated.',
};

/** Part positions as percentages of the square cut, from the KiCad file. */
export const plateParts = PARTS.map((p: BoardPart) => {
  const [fx, fy] = toFrame(p.x, p.y);
  return {
    ref: p.ref,
    label: p.label,
    group: p.group,
    x: ((fx - SAARTHI_CUT.left) / SAARTHI_CUT.size) * 100,
    y: ((fy - SAARTHI_CUT.top) / SAARTHI_CUT.size) * 100,
  };
});

// Guard: the cut must stay inside the 2400 × 1600 frame.
if (SAARTHI_CUT.left + SAARTHI_CUT.size > HERO_FRAME.width) throw new Error('SAARTHI_CUT overflow');

// ---------- TESSERA: cells of the held-out results grid ----------
const cells = import.meta.glob<ImageMetadata>('../assets/work/derived/tessera-*.png', {
  eager: true,
  import: 'default',
});
const cell = (scene: string, col: string) => {
  const img = cells[`../assets/work/derived/tessera-${scene}-${col}.png`];
  if (!img) throw new Error(`Missing TESSERA crop ${scene}-${col}: run scripts/crop-evidence.mjs`);
  return img;
};

/** Row labels exactly as the grid prints them. */
export const TESSERA_SCENES = [
  { id: 'forest', label: 'Forest/vegetation proxy (test)' },
  { id: 'agriculture', label: 'Agriculture (test)' },
  { id: 'urban', label: 'Urban/coastal proxy (test)' },
  { id: 'water', label: 'Water/coast (test)' },
  { id: 'desert', label: 'Desert/bare soil (test)' },
] as const;

/** Columns in pipeline order. `panel` is the grid's own heading. */
export const TESSERA_COLUMNS = [
  { id: 'thermal', panel: 'ST_B10 thermal', role: 'Input' },
  { id: 'tessera', panel: 'TESSERA RGB', role: 'Output' },
  { id: 'risk', panel: 'TESSERA risk', role: 'Risk map' },
  { id: 'truth', panel: 'Ground truth RGB', role: 'For comparison' },
] as const;

export const tesseraScenes = TESSERA_SCENES.map((s) => ({
  ...s,
  cells: TESSERA_COLUMNS.map((c) => ({ ...c, src: cell(s.id, c.id) })),
}));

export const TESSERA_SOURCE =
  'Held-out Landsat test scenes, cropped from the results grid. The model sees only the thermal band; ground truth is shown for comparison. The risk map marks where the colour is not supported by the input.';
