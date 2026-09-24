// Placeholder art: a generated PCB layout (IC footprints, 45° routed traces, drilled pads) in
// --rule on --surface, rasterised to JPG so it runs through the same AVIF/JPG pipeline as the
// real photos. Seeded per slot, so every placeholder is distinct and stable between runs.
// hero-xray reuses the hero-photo seed in --oxblood-hi on --bg: the same layout, pixel-aligned,
// which is what the real KiCad plot will be relative to the real photo.
// Every file here is TODO(vedant): replace with the real photo/render.
// Run: node scripts/placeholders.mjs
import sharp from 'sharp';

const SURFACE_ = '#1e1916';
const RULE_ = '#352c27';
const BG = '#14100e';
const OXBLOOD_HI = '#e25964';
const out = 'src/assets/placeholders';

// [file, width, height, seed?, palette?]
const slots = [
  ['hero-photo', 2400, 1600],
  ['hero-xray', 2400, 1600, 'hero-photo', 'xray'],
  ['saarthi-cover', 1600, 1200],
  ['prahari-cover', 1600, 1200],
  ['vajra-cover', 1600, 1200],
  ['skynet-cover', 1200, 1600],
  ['fusion-artifact', 1600, 1000],
  ['about-portrait', 1200, 1500],
  ['hall-saarthi', 1200, 1200],
  ['hall-setu', 1200, 1200],
];

function rng(seedText) {
  let a = [...seedText].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 2654435761), 1779033703);
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 8 routing directions, 45° apart: E, SE, S, SW, W, NW, N, NE.
const DIRS = [
  [1, 0],
  [1, 1],
  [0, 1],
  [-1, 1],
  [-1, 0],
  [-1, -1],
  [0, -1],
  [1, -1],
];

function layout(name, w, h, palette = 'photo') {
  const [SURFACE, RULE] = palette === 'xray' ? [BG, OXBLOOD_HI] : [SURFACE_, RULE_];
  const rand = rng(name);
  const g = Math.round(Math.max(w, h) / 48); // grid pitch in px
  const cols = Math.floor(w / g) - 1;
  const rows = Math.floor(h / g) - 1;
  const used = new Set();
  // Diagonal segments claim their grid square so two 45° traces never cross in an X.
  const diag = new Set();
  const sq = (x, y, dx, dy) => `${Math.min(x, x + dx)},${Math.min(y, y + dy)}`;
  const key = (x, y) => `${x},${y}`;
  const free = (x, y) => x > 0 && y > 0 && x < cols && y < rows && !used.has(key(x, y));
  const px = (v) => v * g;
  const parts = [];
  const starts = [];

  // IC footprints: outline plus square pin pads along both long sides.
  const ics = 2 + Math.floor(rand() * 3);
  for (let i = 0; i < ics; i++) {
    const iw = 4 + Math.floor(rand() * 5);
    const ih = 3 + Math.floor(rand() * 4);
    const x0 = 2 + Math.floor(rand() * (cols - iw - 4));
    const y0 = 2 + Math.floor(rand() * (rows - ih - 4));
    let clear = true;
    for (let x = x0 - 1; x <= x0 + iw + 1; x++)
      for (let y = y0 - 1; y <= y0 + ih + 1; y++) if (used.has(key(x, y))) clear = false;
    if (!clear) continue;
    for (let x = x0 - 1; x <= x0 + iw + 1; x++)
      for (let y = y0 - 1; y <= y0 + ih + 1; y++) used.add(key(x, y));
    parts.push(
      `<rect x="${px(x0)}" y="${px(y0)}" width="${px(iw)}" height="${px(ih)}" fill="none" stroke="${RULE}" stroke-width="${g * 0.16}"/>`,
    );
    const s = g * 0.42;
    for (let x = x0; x <= x0 + iw; x++) {
      for (const [y, dy] of [
        [y0 - 1, -1],
        [y0 + ih + 1, 1],
      ]) {
        parts.push(
          `<rect x="${px(x) - s / 2}" y="${px(y) - s / 2}" width="${s}" height="${s}" fill="${RULE}"/>`,
        );
        if (rand() < 0.55) starts.push({ x, y, d: dy < 0 ? 6 : 2, pin: true });
      }
    }
  }

  // Free-standing trace starts.
  const loose = Math.floor((cols * rows) / 30);
  for (let i = 0; i < loose; i++) {
    starts.push({
      x: 1 + Math.floor(rand() * (cols - 1)),
      y: 1 + Math.floor(rand() * (rows - 1)),
      d: Math.floor(rand() * 8),
      pin: false,
    });
  }

  // Route: walk the grid, turning ±45° now and then, stopping before any occupied cell.
  for (const s of starts) {
    let { x, y, d } = s;
    if (!s.pin && !free(x, y)) continue;
    const pts = [[x, y]];
    const cells = s.pin ? [] : [key(x, y)];
    const squares = [];
    const max = 6 + Math.floor(rand() * 22);
    let steps = 0;
    for (let step = 0; step < max; step++) {
      if (step > 1 && rand() < 0.22) d = (d + (rand() < 0.5 ? 1 : 7)) % 8;
      const [dx, dy] = DIRS[d];
      if (!free(x + dx, y + dy)) break;
      if (dx && dy && diag.has(sq(x, y, dx, dy))) break;
      if (dx && dy) squares.push(sq(x, y, dx, dy));
      x += dx;
      y += dy;
      cells.push(key(x, y));
      steps++;
      // Merge collinear points so each run is one segment with a clean mitred corner.
      const last = pts[pts.length - 1];
      const prev = pts[pts.length - 2];
      if (prev && Math.sign(last[0] - prev[0]) === dx && Math.sign(last[1] - prev[1]) === dy)
        pts.pop();
      pts.push([x, y]);
    }
    if (steps < 3) continue;
    cells.forEach((c) => used.add(c));
    squares.forEach((q) => diag.add(q));
    const d2 = pts.map(([a, b], i) => `${i ? 'L' : 'M'}${px(a)} ${px(b)}`).join(' ');
    parts.push(
      `<path d="${d2}" fill="none" stroke="${RULE}" stroke-width="${g * 0.2}" stroke-linejoin="miter" stroke-linecap="round"/>`,
    );
    const ends = s.pin ? [pts[pts.length - 1]] : [pts[0], pts[pts.length - 1]];
    for (const [a, b] of ends) {
      parts.push(`<circle cx="${px(a)}" cy="${px(b)}" r="${g * 0.36}" fill="${RULE}"/>`);
      parts.push(`<circle cx="${px(a)}" cy="${px(b)}" r="${g * 0.14}" fill="${SURFACE}"/>`);
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="${SURFACE}"/>${parts.join('')}</svg>`;
}

for (const [name, w, h, seed = name, palette] of slots) {
  const svg = layout(seed, w, h, palette);
  const info = await sharp(Buffer.from(svg))
    .jpeg({ quality: 78, mozjpeg: true })
    .toFile(`${out}/${name}.jpg`);
  console.log(`${name}.jpg ${w}x${h} ${(info.size / 1024).toFixed(1)} KB`);
}
