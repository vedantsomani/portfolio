// Which element is the LCP on each route (Lighthouse mobile, one run): for chasing the 2.0 s budget.
// Usage: node scripts/qa/lcp-element.mjs /route [/route…]
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import { BASE } from './routes.mjs';

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const chrome = await chromeLauncher.launch({
  chromePath: process.env.CHROME_PATH ?? EDGE,
  chromeFlags: ['--headless=new', '--no-first-run'],
});
for (const route of process.argv.slice(2)) {
  const { lhr } = await lighthouse(BASE + route, {
    port: chrome.port,
    onlyCategories: ['performance'],
    output: 'json',
  });
  // Lighthouse 12+: the element and its phases live in the LCP breakdown insight.
  const bd = lhr.audits['lcp-breakdown-insight']?.details?.items ?? [];
  const items = bd.flatMap((i) => (i.type === 'list' ? i.items : [i]));
  const el = items.find((i) => i.type === 'node') ?? items.find((i) => i.node)?.node;
  const phases = items.find((i) => i.type === 'table')?.items ?? [];
  const a = lhr.audits;
  console.log(
    route,
    a['largest-contentful-paint'].displayValue,
    `(FCP ${a['first-contentful-paint'].displayValue}, TBT ${a['total-blocking-time'].displayValue}, main thread ${a['mainthread-work-breakdown']?.displayValue ?? '?'})`,
    '\n  ',
    el?.snippet,
    '\n  ',
    phases.map((p) => `${p.label ?? p.subpart ?? p.phase} ${Math.round(p.duration ?? p.timing)}ms`).join(', '),
    el ? '' : JSON.stringify(items).slice(0, 600),
  );
}
try {
  chrome.kill();
} catch {
  /* Windows sometimes holds the profile folder a moment longer */
}
