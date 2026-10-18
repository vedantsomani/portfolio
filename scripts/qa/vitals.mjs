// Field-style first paint and LCP: each route loaded in a real browser with applied throttling
// (150 ms latency, 1.6 Mbps down, 750 kbps up, 4x CPU), a phone viewport, and a fresh session (so
// home plays its cold open, as for a first-time visitor). Lighthouse's simulated numbers
// (lighthouse.mjs) are the budget of record; this shows what a slow phone actually gets.
// Usage: node scripts/qa/vitals.mjs [route…]
import { chromium } from 'playwright';
import { BASE, ROUTES } from './routes.mjs';

const routes = process.argv.slice(2).length ? process.argv.slice(2) : ROUTES;
const browser = await chromium.launch({ channel: 'msedge' });
for (const route of routes) {
  const ctx = await browser.newContext({
    viewport: { width: 412, height: 823 },
    deviceScaleFactor: 1.75,
    isMobile: true,
  });
  const page = await ctx.newPage();
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false,
    latency: 150,
    downloadThroughput: (1.6 * 1024 * 1024) / 8,
    uploadThroughput: (750 * 1024) / 8,
  });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await page.addInitScript(() => {
    window.__lcp = [];
    new PerformanceObserver((list) => window.__lcp.push(...list.getEntries())).observe({
      type: 'largest-contentful-paint',
      buffered: true,
    });
  });
  await page.goto(BASE + route, { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  const r = await page.evaluate(() => {
    const fcp = performance.getEntriesByName('first-contentful-paint')[0]?.startTime ?? 0;
    const lcp = window.__lcp.at(-1);
    return { fcp, lcp: lcp?.startTime ?? 0, el: lcp?.element?.tagName ?? '?' };
  });
  const ok = r.lcp <= 2000;
  console.log(
    `${ok ? 'PASS' : 'FAIL'}  ${route.padEnd(28)} FCP ${(r.fcp / 1000).toFixed(2)} s  LCP ${(r.lcp / 1000).toFixed(2)} s (${r.el})`,
  );
  await ctx.close();
}
await browser.close();
