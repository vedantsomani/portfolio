// Check 4: HTTP status of every route against the production build under wrangler dev.
import { BASE, NOT_FOUND, ROUTES } from './routes.mjs';

const rows = [];
let ok = true;
const probe = async (path, expect, location) => {
  const res = await fetch(BASE + path, { redirect: 'manual' });
  const loc = res.headers.get('location');
  const pass =
    res.status === expect &&
    (location === undefined || new URL(loc ?? '', BASE).pathname === location);
  ok &&= pass;
  rows.push(
    `${pass ? 'PASS' : 'FAIL'}  ${String(res.status).padEnd(4)} ${path}${loc ? `  → ${loc}` : ''}`,
  );
};
for (const r of ROUTES) await probe(r, 200);
await probe(NOT_FOUND, 404);
await probe('/services', 301, '/');
await probe('/projects/prahari', 301, '/lab/prahari');
console.log(rows.join('\n'));
if (!ok) process.exit(1);
