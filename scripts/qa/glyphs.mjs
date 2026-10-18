// Glyph coverage: every character a built page sets must be in the Archivo subset
// (UNICODES in scripts/subset-fonts.py), or render in IBM Plex Mono. Anything else would fall back
// to a system font without anyone noticing. Reads the built HTML; run after `npm run build`.
// Usage: node scripts/qa/glyphs.mjs
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const py = readFileSync('scripts/subset-fonts.py', 'utf8');
const line = py.match(/^UNICODES = "([^"]+)"/m)?.[1];
if (!line) throw new Error('UNICODES not found in scripts/subset-fonts.py');
const ranges = line.split(',').map((r) => {
  const [a, b] = r.replace(/U\+/g, '').split('-');
  return [parseInt(a, 16), parseInt(b ?? a, 16)];
});
const covered = (cp) => cp < 0x20 || ranges.some(([a, b]) => cp >= a && cp <= b);

// Visible text only: drop scripts, styles, JSON-LD, and tags; decode the entities Astro emits.
const text = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/g, ' ')
    .replace(/<style[\s\S]*?<\/style>/g, ' ')
    .replace(/<svg[\s\S]*?<\/svg>/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, ' ');

const files = [];
const walk = (d) => {
  for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (f.endsWith('.html')) files.push(p);
  }
};
walk('dist/client');

const missing = new Map();
for (const f of files) {
  for (const ch of text(readFileSync(f, 'utf8'))) {
    const cp = ch.codePointAt(0);
    if (!covered(cp)) missing.set(ch, [...(missing.get(ch) ?? []), f]);
  }
}
if (!missing.size) {
  console.log(`PASS  every character on ${files.length} pages is in the Archivo subset`);
} else {
  for (const [ch, where] of missing) {
    const cp = 'U+' + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
    console.log(`WARN  ${cp} "${ch}" not in the subset (falls back unless set in Plex Mono): ${[...new Set(where)].slice(0, 3).join(', ')}`);
  }
}
