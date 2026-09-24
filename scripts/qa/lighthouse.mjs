// Check 5: Lighthouse mobile (default mobile emulation + simulated 4G throttling) on every route,
// run against wrangler dev with PRE_LAUNCH off (npm run preview:audit). Uses the system Edge.
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import { writeFileSync } from 'node:fs';
import { BASE, ROUTES } from './routes.mjs';

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const routes = process.argv.slice(2).length ? process.argv.slice(2) : ROUTES;
const chrome = await chromeLauncher.launch({
  chromePath: process.env.CHROME_PATH ?? EDGE,
  chromeFlags: ['--headless=new', '--no-first-run'],
});

const rows = [];
let ok = true;
for (const route of routes) {
  const { lhr } = await lighthouse(BASE + route, {
    port: chrome.port,
    output: 'json',
    logLevel: 'error',
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
  });
  const s = (k) => Math.round(lhr.categories[k].score * 100);
  const lcp = lhr.audits['largest-contentful-paint'].numericValue / 1000;
  const cls = lhr.audits['cumulative-layout-shift'].numericValue;
  const row = {
    route,
    perf: s('performance'),
    a11y: s('accessibility'),
    bp: s('best-practices'),
    seo: s('seo'),
    lcp: lcp.toFixed(2),
    cls: cls.toFixed(3),
  };
  const pass =
    row.perf >= 95 &&
    row.a11y === 100 &&
    row.bp === 100 &&
    row.seo === 100 &&
    lcp <= 2 &&
    cls <= 0.05;
  ok &&= pass;
  rows.push(Object.assign(row, { pass }));
  if (!pass) {
    const failing = Object.values(lhr.audits)
      .filter(
        (a) =>
          a.score !== null &&
          a.score < 1 &&
          a.scoreDisplayMode !== 'informative' &&
          a.scoreDisplayMode !== 'manual',
      )
      .map((a) => `${a.id} (${a.displayValue ?? a.score})`);
    row.failing = failing.slice(0, 12).join(', ');
  }
}
const line = (c) => `| ${c.join(' | ')} |`;
console.log(line(['Route', 'Perf', 'A11y', 'BP', 'SEO', 'LCP s', 'CLS', '']));
console.log(line(['---', '---', '---', '---', '---', '---', '---', '---']));
for (const r of rows)
  console.log(line([r.route, r.perf, r.a11y, r.bp, r.seo, r.lcp, r.cls, r.pass ? 'PASS' : 'FAIL']));
for (const r of rows) if (r.failing) console.log(`\n${r.route} below 1: ${r.failing}`);
writeFileSync('qa/final/lighthouse.json', JSON.stringify(rows, null, 2));
try {
  chrome.kill();
} catch {
  // Windows: chrome-launcher cannot always delete its temp profile. Harmless.
}
if (!ok) process.exit(1);
