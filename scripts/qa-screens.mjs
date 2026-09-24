// Full-page screenshots at 375 / 768 / 1440 plus layout probes and an axe scan.
// Usage: node scripts/qa-screens.mjs [baseURL]   (default http://localhost:4321)
// Uses the system Edge (Playwright channel "msedge"), so no browser download is needed.
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const base = process.argv[2] ?? 'http://localhost:4321';
const routes = ['/', '/services', '/contact', '/this-page-does-not-exist'];
const widths = [375, 768, 1440];
mkdirSync('qa', { recursive: true });

const browser = await chromium.launch({ channel: 'msedge' });
const report = {};

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  const page = await context.newPage();
  for (const route of routes) {
    await page.goto(base + route, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const name = route === '/' ? 'home' : route.slice(1).replace(/\W+/g, '-');
    await page.screenshot({ path: `qa/${name}-${width}.png`, fullPage: true });

    const probe = await page.evaluate(() => {
      const lines = (el) => {
        if (!el) return null;
        const lh = parseFloat(getComputedStyle(el).lineHeight);
        return Math.round(el.getBoundingClientRect().height / lh);
      };
      const title = document.querySelector('.t-display');
      return {
        overflowX: document.documentElement.scrollWidth > window.innerWidth,
        displaySize: title ? getComputedStyle(title).fontSize : null,
        displayLines: lines(title),
        displayText: title?.textContent?.trim(),
      };
    });
    report[`${name}@${width}`] = probe;

    if (width === 375 || width === 1440) {
      const axe = await new AxeBuilder({ page }).analyze();
      report[`${name}@${width}`].axe = axe.violations.map((v) => `${v.id} (${v.nodes.length})`);
    }
  }
  await context.close();
}

await browser.close();
writeFileSync('qa/report.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
