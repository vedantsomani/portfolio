// Geometry of the placeholder "VEDANT" wordmark (see Wordmark.astro for the construction rules).
// Shared by the component and scripts/og.mjs. Plain JS (JSDoc types) so the OG script runs on any
// Node version without type stripping. TODO(vedant): replace with the final SVG.
/** @typedef {[number, number]} Pt */
/** @typedef {{ paths: Pt[][]; closed?: boolean; pads: Pt[] }} Letter */

/** @type {Letter[]} */
const letters = [
  // V: two stems turn 45° inward and meet at the bottom pad
  {
    paths: [
      [
        [0, 0],
        [0, 6],
        [2, 8],
      ],
      [
        [4, 0],
        [4, 6],
        [2, 8],
      ],
    ],
    pads: [
      [0, 0],
      [4, 0],
      [2, 8],
    ],
  },
  // E: chamfered spine, three arms ending in pads
  {
    paths: [
      [
        [4, 0],
        [1, 0],
        [0, 1],
        [0, 7],
        [1, 8],
        [4, 8],
      ],
      [
        [0, 4],
        [3, 4],
      ],
    ],
    pads: [
      [4, 0],
      [4, 8],
      [3, 4],
    ],
  },
  // D: closed net, 2u chamfers on the bowl, no pads
  {
    paths: [
      [
        [0, 0],
        [2, 0],
        [4, 2],
        [4, 6],
        [2, 8],
        [0, 8],
      ],
    ],
    closed: true,
    pads: [],
  },
  // A: the V inverted, with a crossbar on T-junctions
  {
    paths: [
      [
        [0, 8],
        [0, 2],
        [2, 0],
      ],
      [
        [4, 8],
        [4, 2],
        [2, 0],
      ],
      [
        [0, 5],
        [4, 5],
      ],
    ],
    pads: [
      [0, 8],
      [4, 8],
      [2, 0],
    ],
  },
  // N: full stems, one 45° diagonal from the top of the left stem
  {
    paths: [
      [
        [0, 8],
        [0, 0],
        [4, 4],
      ],
      [
        [4, 0],
        [4, 8],
      ],
    ],
    pads: [
      [0, 8],
      [4, 0],
      [4, 8],
    ],
  },
  // T: bar with pads at both ends, stem on a T-junction
  {
    paths: [
      [
        [0, 0],
        [4, 0],
      ],
      [
        [2, 0],
        [2, 8],
      ],
    ],
    pads: [
      [0, 0],
      [4, 0],
      [2, 8],
    ],
  },
];

const ADVANCE = 7;
const PAD = 1;
/** @type {(pts: Pt[], dx: number, closed?: boolean) => string} */
const toD = (pts, dx, closed) =>
  pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x + dx + PAD} ${y + PAD}`).join(' ') +
  (closed ? ' Z' : '');

/** @type {string[]} */
export const traces = [];
/** @type {Pt[]} */
export const pads = [];
letters.forEach((l, i) => {
  const dx = i * ADVANCE;
  l.paths.forEach((p) => traces.push(toD(p, dx, l.closed)));
  l.pads.forEach(([x, y]) => pads.push([x + dx + PAD, y + PAD]));
});

export const width = 5 * ADVANCE + 4 + 2 * PAD;
export const height = 8 + 2 * PAD;
