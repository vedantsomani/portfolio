// Check 7: initial JS per route (gzip), following static imports only. Dynamic imports (the OGL
// lens on idle, Three.js near the hall, ScrollTrigger/DrawSVG on desktop) are listed separately.
// Three.js must not be in any initial chunk: its bundle sets window.__THREE__.
import { readFileSync, readdirSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join } from 'node:path';
import { BASE, ROUTES, NOT_FOUND } from './routes.mjs';

const CLIENT = 'dist/client';
const LIMIT = 90 * 1024;
const gz = (file) => gzipSync(readFileSync(join(CLIENT, file))).length;
const kb = (n) => `${(n / 1024).toFixed(1)} KB`;

// Static imports in minified ESM: import{..}from"./x.js" / import"./x.js" / export{..}from"./x.js".
const staticDeps = (file) => {
  const src = readFileSync(join(CLIENT, file), 'utf8');
  const dir = file.slice(0, file.lastIndexOf('/') + 1);
  const deps = new Set();
  for (const m of src.matchAll(
    /(?:^|[;}\s])(?:import|export)\s*(?:[\w${},*\s]+from\s*)?["']([^"']+\.js)["']/g,
  ))
    deps.add(new URL(m[1], `http://x/${dir}`).pathname.slice(1));
  return [...deps];
};
const dynamicDeps = (file) => {
  const src = readFileSync(join(CLIENT, file), 'utf8');
  const dir = file.slice(0, file.lastIndexOf('/') + 1);
  return [...src.matchAll(/import\(\s*["']([^"']+\.js)["']\s*\)/g)].map((m) =>
    new URL(m[1], `http://x/${dir}`).pathname.slice(1),
  );
};

let ok = true;
const lazy = new Set();
// HTML as served (the on-demand /contact has no file in dist).
const html = async (r) => (await fetch(BASE + r)).text();
console.log('Initial JS per route (gzip, static import graph):');
for (const route of [...ROUTES, NOT_FOUND]) {
  const page = await html(route);
  const entries = new Set();
  for (const m of page.matchAll(/<script[^>]+type="module"[^>]+src="\/([^"]+)"/g))
    entries.add(m[1]);
  for (const m of page.matchAll(/<link[^>]+rel="modulepreload"[^>]+href="\/([^"]+)"/g))
    entries.add(m[1]);
  for (const m of page.matchAll(/<script type="module">([\s\S]*?)<\/script>/g))
    for (const i of m[1].matchAll(/["']\/(_astro\/[^"']+\.js)["']/g)) entries.add(i[1]);
  const seen = new Set();
  const walk = (f) => {
    if (seen.has(f)) return;
    seen.add(f);
    staticDeps(f).forEach(walk);
    dynamicDeps(f).forEach((d) => lazy.add(d));
  };
  entries.forEach(walk);
  const total = [...seen].reduce((sum, f) => sum + gz(f), 0);
  const three = [...seen].filter((f) =>
    readFileSync(join(CLIENT, f), 'utf8').includes('__THREE__'),
  );
  const pass = total <= LIMIT && three.length === 0;
  ok &&= pass;
  console.log(
    `${pass ? 'PASS' : 'FAIL'}  ${route.padEnd(28)} ${kb(total).padStart(8)}  ${seen.size} files  three.js in initial: ${three.length ? three.join(',') : 'no'}`,
  );
}
console.log('\nLazy chunks (loaded later, not initial):');
const walkLazy = new Set();
const addLazy = (f) => {
  if (walkLazy.has(f)) return;
  walkLazy.add(f);
  staticDeps(f).forEach(addLazy);
  dynamicDeps(f).forEach(addLazy);
};
lazy.forEach(addLazy);
for (const f of [...walkLazy].sort()) {
  const three = readFileSync(join(CLIENT, f), 'utf8').includes('__THREE__');
  console.log(`      ${f.padEnd(52)} ${kb(gz(f)).padStart(8)}${three ? '  (three.js)' : ''}`);
}
const glbs = readdirSync(join(CLIENT)).includes('models')
  ? readdirSync(join(CLIENT, 'models'))
  : [];
console.log(
  `\nGLB files in the build: ${glbs.length ? glbs.join(', ') : 'none yet (procedural placeholders)'}`,
);
if (!ok) process.exit(1);
