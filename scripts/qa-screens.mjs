// Full-page screenshots at 375 / 768 / 1440 for every route, plus layout probes.
// Usage: node scripts/qa-screens.mjs [baseURL] [outDir]   (default http://localhost:4321, qa)
// Uses the system Edge (Playwright channel "msedge"), so no browser download is needed.
// Each page is scrolled top to bottom first so lazy images, the hall, and scroll moments settle,
// and the capture is taken at the bottom so the scroll-drawn signal trace shows in full. A full-page
// capture has no single scroll position, so the scroll-linked cover wipe is pinned to its end
// state and the fixed nav is drawn at the top of the capture (the stylesheet below); every other
// pixel is the page as served.
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const base = process.argv[2] ?? 'http://localhost:4321';
const out = process.argv[3] ?? 'qa';
export const ROUTES = [
  '/',
  '/projects',
  '/projects/saarthi',
  '/projects/tessera',
  '/projects/anav',
  '/projects/vajra',
  '/projects/smriti',
  '/projects/dhwani-kavach',
  '/projects/pitsense',
  '/projects/iot-club-website',
  '/lab',
  '/lab/skynet',
  '/lab/prahari',
  '/about',
  '/contact',
  '/this-page-does-not-exist',
];
const widths = [375, 768, 1440];
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ channel: 'msedge' });
const report = {};

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  const page = await context.newPage();
  for (const route of routes()) {
    await page.goto(base + route, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 400) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 60));
      }
      await new Promise((r) => setTimeout(r, 1600));
    });
    await page.addStyleTag({
      content:
        '.cover-wipe { animation: none !important; } .nav { position: absolute !important; }',
    });
    const name = route === '/' ? 'home' : route.slice(1).replace(/\W+/g, '-');
    await page.screenshot({ path: `${out}/${name}-${width}.png`, fullPage: true });
    report[`${name}@${width}`] = await page.evaluate(() => ({
      overflowX: document.documentElement.scrollWidth > window.innerWidth,
      h1: document.querySelector('h1')?.textContent?.trim().slice(0, 60),
    }));
  }
  await context.close();
}

function routes() {
  return ROUTES;
}

await browser.close();
writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
