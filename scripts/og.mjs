// Open Graph images, generated before `astro build` (npm run build runs this first): Satori lays
// out the design tokens and the PCB wordmark, sharp rasterises the SVG to PNG. One image per page
// and per project / lab entry, written to public/og/<key>.png (committed, so a build that skips
// this script still ships them).
// Run: node scripts/og.mjs
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import satori from 'satori';
import sharp from 'sharp';
import { parse } from 'yaml';
import { height, pads, traces, width } from '../src/lib/wordmark.js';

const BG = '#14100e';
const INK = '#f2ebe4';
const INK2 = '#a99d93';
const OXBLOOD = '#5a1e14';
const OUT = 'public/og';

const fonts = [
  {
    name: 'Archivo Display',
    data: readFileSync('scripts/og-fonts/archivo-display.ttf'),
    weight: 800,
  },
  { name: 'Archivo', data: readFileSync('scripts/og-fonts/archivo-body.ttf'), weight: 500 },
];

const frontmatter = (file) => parse(readFileSync(file, 'utf8').split(/^---$/m)[1]);
const collection = (dir) =>
  readdirSync(dir)
    .filter((f) => f.endsWith('.mdx'))
    .map((f) => frontmatter(`${dir}/${f}`));

const pages = [
  {
    key: 'home',
    title: 'Flight controllers, autonomy, and secure comms.',
    kicker: 'Built from the silicon up',
  },
  { key: 'projects', title: 'Projects', kicker: 'Saarthi, PRAHARI, VAJRA' },
  { key: 'lab', title: 'Lab', kicker: 'Hardware hall and build log' },
  { key: 'about', title: 'About', kicker: 'CSE, Bennett University' },
  { key: 'contact', title: 'Get in touch', kicker: 'Internships, research, hardware' },
  ...collection('src/content/projects').map((p) => ({
    key: `project-${p.slug}`,
    title: p.title,
    kicker: p.summary,
  })),
  ...collection('src/content/lab').map((e) => ({
    key: `lab-${e.slug}`,
    title: e.title,
    kicker: e.discipline,
  })),
];

const h = (type, style, children, extra = {}) => ({ type, props: { style, children, ...extra } });

// The wordmark as SVG children: traces, pads, and drills (drawn as --bg dots over the pads).
const scale = 9;
const wordmark = h(
  'svg',
  { width: width * scale, height: height * scale },
  [
    ...traces.map((d) =>
      h('path', {}, undefined, {
        d,
        fill: 'none',
        stroke: INK,
        strokeWidth: 1,
        strokeLinejoin: 'miter',
        strokeLinecap: 'square',
      }),
    ),
    ...pads.map(([x, y]) => h('circle', {}, undefined, { cx: x, cy: y, r: 1, fill: INK })),
    ...pads.map(([x, y]) => h('circle', {}, undefined, { cx: x, cy: y, r: 0.45, fill: BG })),
  ],
  { viewBox: `0 0 ${width} ${height}` },
);

function card({ title, kicker }) {
  const size = title.length > 36 ? 64 : title.length > 18 ? 84 : 112;
  return h(
    'div',
    { width: 1200, height: 630, display: 'flex', background: BG, fontFamily: 'Archivo' },
    [
      h(
        'div',
        {
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          width: 840,
          padding: '64px 0 64px 72px',
        },
        [
          wordmark,
          h('div', { display: 'flex', flexDirection: 'column', gap: 24 }, [
            h(
              'div',
              {
                fontFamily: 'Archivo Display',
                fontSize: size,
                lineHeight: 0.95,
                letterSpacing: '-0.035em',
                color: INK,
              },
              title,
            ),
            h('div', { fontSize: 30, color: INK2, lineHeight: 1.3 }, kicker),
          ]),
        ],
      ),
      // The owned colour as a field, never a thin accent.
      h('div', { display: 'flex', flex: 1, background: OXBLOOD, marginLeft: 48 }, []),
    ],
  );
}

mkdirSync(OUT, { recursive: true });
for (const page of pages) {
  const svg = await satori(card(page), { width: 1200, height: 630, fonts });
  const png = await sharp(Buffer.from(svg)).png({ compressionLevel: 9 }).toBuffer();
  writeFileSync(`${OUT}/${page.key}.png`, png);
  console.log(`og/${page.key}.png ${(png.length / 1024).toFixed(1)} KB`);
}
