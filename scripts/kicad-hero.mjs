// Hero photo + x-ray from ONE KiCad board file, pixel-aligned through the mounting holes.
//   1. kicad-cli renders the board top-down (orthographic, transparent) and plots F.Cu, B.Cu and
//      F.Silkscreen as SVG (board area only, so SVG units are mm from the Edge.Cuts corner).
//   2. The drilled holes are found in the render (dark components inside the board) and a
//      px = s·mm + t fit is solved against the four outermost MountingHole footprints in the file.
//      Every other mounting hole is checked against the fit; the run fails above 1 px of error.
//   3. Both layers are composed on one 2400×1600 --bg canvas, clear of the headline (see BOARD_PX).
// Output: src/assets/work/saarthi-hero.jpg and saarthi-xray.jpg. Also run `kicad-cli pcb export glb`
// on the same file for public/models/saarthi.glb (see ASSETS.md), so the hall shows the same board.
// Run: node scripts/kicad-hero.mjs <board.kicad_pcb>   (KICAD_CLI overrides the kicad-cli path)
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import sharp from 'sharp';

const pcb = process.argv[2];
if (!pcb) throw new Error('Usage: node scripts/kicad-hero.mjs <board.kicad_pcb>');
const cli = process.env.KICAD_CLI ?? 'kicad-cli';
const work = mkdtempSync(join(tmpdir(), 'kicad-hero-'));
const OUT = 'src/assets/work';
const BG = { r: 0x14, g: 0x10, b: 0x0e, alpha: 1 };
const COPPER = '#E25964'; // --oxblood-hi (imagery is exempt from the red rule, SITE_SPEC §3)
const SILK = '#A99D93'; // --ink-2
const CW = 2400;
const CH = 1600;
// Placement, measured against the live hero: on desktop the lens box is portrait (e.g. 708×828 at
// 1440 px) with object-fit: cover, so only the middle of the 3:2 frame shows (source x ≈ 516–1884
// at 1440, 715–1685 at 1024), and the headline reaches source x ≈ 890–980. The board therefore
// sits at x 1000–1860, right of the headline and inside the mobile 4:3 centre crop.
const BOARD_PX = 860; // board height on the canvas
const BOARD_RIGHT = 1860;

// --- Board geometry from the file ---------------------------------------------------------------
const src = readFileSync(pcb, 'utf8');
const holesMm = [
  ...src.matchAll(/\(footprint "MountingHole[^"]*"[\s\S]*?\(at ([-\d.]+) ([-\d.]+)/g),
].map((m) => [Number(m[1]), Number(m[2])]);
const edge = [
  ...src.matchAll(/\((?:gr_line|gr_arc|gr_poly|gr_rect)([\s\S]*?)\(layer "Edge\.Cuts"\)/g),
]
  .flatMap((m) => [...m[1].matchAll(/\((?:start|end|mid|xy) ([-\d.]+) ([-\d.]+)\)/g)])
  .map((m) => [Number(m[1]), Number(m[2])]);
const ex0 = Math.min(...edge.map((p) => p[0]));
const ey0 = Math.min(...edge.map((p) => p[1]));
const boardW = Math.max(...edge.map((p) => p[0])) - ex0;
const boardH = Math.max(...edge.map((p) => p[1])) - ey0;
const extreme = (fx, fy) => holesMm.reduce((a, b) => (fx(b) + fy(b) < fx(a) + fy(a) ? b : a));
const outerMm = [
  extreme(
    (h) => h[0],
    (h) => h[1],
  ),
  extreme(
    (h) => -h[0],
    (h) => h[1],
  ),
  extreme(
    (h) => h[0],
    (h) => -h[1],
  ),
  extreme(
    (h) => -h[0],
    (h) => -h[1],
  ),
];

// --- KiCad outputs ------------------------------------------------------------------------------
const run = (...args) => execFileSync(cli, args, { stdio: 'pipe' });
const top = join(work, 'top.png');
run(
  'pcb',
  'render',
  '-o',
  top,
  '-w',
  '2400',
  '-h',
  '2400',
  '--side',
  'top',
  '--background',
  'transparent',
  '--quality',
  'high',
  pcb,
);
const svg = (layer) => {
  const file = join(work, `${layer}.svg`);
  run(
    'pcb',
    'export',
    'svg',
    '-o',
    file,
    '--layers',
    layer,
    '--mode-single',
    '--page-size-mode',
    '2',
    '--exclude-drawing-sheet',
    '--black-and-white',
    pcb,
  );
  return readFileSync(file, 'utf8');
};

// --- Find the holes in the render -----------------------------------------------------------------
const { data, info } = await sharp(top).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
const { width: W, height: H } = info;
const transparent = (i) => data[i * 4 + 3] < 128;
const dark = (i) => !transparent(i) && data[i * 4] + data[i * 4 + 1] + data[i * 4 + 2] < 45;
const flood = (start, accept, mark, visit) => {
  const stack = [start];
  while (stack.length) {
    const i = stack.pop();
    if (mark[i] || !accept(i)) continue;
    mark[i] = 1;
    visit?.(i);
    const x = i % W;
    if (x > 0) stack.push(i - 1);
    if (x < W - 1) stack.push(i + 1);
    if (i >= W) stack.push(i - W);
    if (i < W * (H - 1)) stack.push(i + W);
  }
};
const outside = new Uint8Array(W * H);
for (let x = 0; x < W; x++) {
  flood(x, transparent, outside);
  flood((H - 1) * W + x, transparent, outside);
}
for (let y = 0; y < H; y++) {
  flood(y * W, transparent, outside);
  flood(y * W + W - 1, transparent, outside);
}
const seen = new Uint8Array(W * H);
const holes = [];
for (let i = 0; i < W * H; i++) {
  if (seen[i] || outside[i] || !dark(i)) continue;
  let n = 0;
  let sx = 0;
  let sy = 0;
  flood(
    i,
    (j) => !outside[j] && dark(j),
    seen,
    (j) => {
      n++;
      sx += j % W;
      sy += (j / W) | 0;
    },
  );
  if (n > 1500 && n < 20000) holes.push({ x: sx / n, y: sy / n });
}
const nearest = (x, y) =>
  holes.reduce((a, b) => (Math.hypot(b.x - x, b.y - y) < Math.hypot(a.x - x, a.y - y) ? b : a));
const extremePx = (fx, fy) => holes.reduce((a, b) => (fx(b) + fy(b) < fx(a) + fy(a) ? b : a));
const outerPx = [
  extremePx(
    (h) => h.x,
    (h) => h.y,
  ),
  extremePx(
    (h) => -h.x,
    (h) => h.y,
  ),
  extremePx(
    (h) => h.x,
    (h) => -h.y,
  ),
  extremePx(
    (h) => -h.x,
    (h) => -h.y,
  ),
];

// --- Fit px = s·mm + t (orthographic top view: one scale, no rotation) ---------------------------
const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
const mx = mean(outerMm.map((p) => p[0]));
const my = mean(outerMm.map((p) => p[1]));
const px = mean(outerPx.map((p) => p.x));
const py = mean(outerPx.map((p) => p.y));
let num = 0;
let den = 0;
outerMm.forEach(([x, y], k) => {
  num += (x - mx) * (outerPx[k].x - px) + (y - my) * (outerPx[k].y - py);
  den += (x - mx) ** 2 + (y - my) ** 2;
});
const s = num / den;
const tx = px - s * mx;
const ty = py - s * my;
const errors = holesMm.map(([x, y]) => {
  const h = nearest(s * x + tx, s * y + ty);
  return Math.hypot(h.x - (s * x + tx), h.y - (s * y + ty));
});
console.log(
  `fit ${s.toFixed(4)} px/mm; hole errors (px): ${errors.map((e) => e.toFixed(2)).join(', ')}`,
);
if (Math.max(...errors) > 1) throw new Error('Mounting-hole alignment error above 1 px');

// --- Compose --------------------------------------------------------------------------------------
const k = BOARD_PX / (boardH * s); // render px → canvas px
const ox = Math.round(BOARD_RIGHT - (boardW / boardH) * BOARD_PX - (s * ex0 + tx) * k);
const oy = Math.round((CH - BOARD_PX) / 2 - (s * ey0 + ty) * k);
const S = s * k; // canvas px per mm
const place = async (buf, left, top) => {
  const { width: bw, height: bh } = await sharp(buf).metadata();
  const l = Math.max(0, -left);
  const t = Math.max(0, -top);
  const w = Math.min(bw - l, CW - Math.max(left, 0));
  const h = Math.min(bh - t, CH - Math.max(top, 0));
  const input = await sharp(buf).extract({ left: l, top: t, width: w, height: h }).png().toBuffer();
  return { input, left: Math.max(left, 0), top: Math.max(top, 0) };
};
const canvas = () => sharp({ create: { width: CW, height: CH, channels: 4, background: BG } });
const save = (img, name) =>
  img.flatten({ background: BG }).jpeg({ quality: 92, mozjpeg: true }).toFile(`${OUT}/${name}`);

const render = await sharp(top)
  .resize(Math.round(W * k), Math.round(H * k))
  .png()
  .toBuffer();
await save(canvas().composite([await place(render, ox, oy)]), 'saarthi-hero.jpg');

// The SVG viewBox is the Edge.Cuts box; KiCad trims a hair off the outline width, split evenly.
const layer = async (name, colour, alpha = 1) => {
  let text = svg(name).replaceAll('#000000', colour);
  const view = Number(/viewBox="[\d.]+ [\d.]+ ([\d.]+)/.exec(text)[1]);
  const size = Math.round(view * S);
  text = text.replace(/width="[\d.]+mm" height="[\d.]+mm"/, `width="${size}" height="${size}"`);
  const { data: d, info: i } = await sharp(Buffer.from(text))
    .resize(size, size)
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  for (let p = 3; p < d.length; p += 4) d[p] = Math.round(d[p] * alpha);
  const buf = await sharp(d, { raw: i }).png().toBuffer();
  const inset = (boardW - view) / 2;
  return place(
    buf,
    Math.round(ox + (s * (ex0 + inset) + tx) * k),
    Math.round(oy + (s * (ey0 + inset) + ty) * k),
  );
};
await save(
  canvas().composite([
    await layer('B.Cu', COPPER, 0.3),
    await layer('F.Cu', COPPER),
    await layer('F.Silkscreen', SILK),
  ]),
  'saarthi-xray.jpg',
);
// Mobile: its own 4:3 cut around the board (identical box for both layers, so the lens stays
// aligned). The board fills 70 % of the height with the lower quarter left for the caption overlay.
const boardLeft = BOARD_RIGHT - (boardW / boardH) * BOARD_PX;
const mh = Math.round(BOARD_PX / 0.7);
const mw = Math.round((mh * 4) / 3);
const mobile = {
  left: Math.round(boardLeft + ((boardW / boardH) * BOARD_PX) / 2 - mw / 2),
  top: Math.round((CH - BOARD_PX) / 2 - mh * 0.05),
  width: mw,
  height: mh,
};
for (const name of ['saarthi-hero', 'saarthi-xray']) {
  await sharp(`${OUT}/${name}.jpg`)
    .extract(mobile)
    .jpeg({ quality: 92, mozjpeg: true })
    .toFile(`${OUT}/${name}-mobile.jpg`);
}
console.log(`wrote ${OUT}/saarthi-{hero,xray}{,-mobile}.jpg (${S.toFixed(3)} px/mm)`);
