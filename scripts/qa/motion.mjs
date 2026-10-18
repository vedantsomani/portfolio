// Motion walkthrough: timed viewport captures of the chapter arrivals, the hero boot, the index
// hover, and the scroll scans, so motion is judged in motion. Screens to qa/motion/.
// Usage: node scripts/qa/motion.mjs [baseURL]   (preview on :8787; system Edge, SwiftShader GL)
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const base = process.argv[2] ?? 'http://127.0.0.1:8787';
const out = 'qa/motion';
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({
  channel: 'msedge',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
await ctx.addInitScript(() => sessionStorage.setItem('intro-seen', '1'));
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
const shot = (name) => page.screenshot({ path: `${out}/${name}.png` });

// Chapter arrivals.
for (const [route, name] of [
  ['/projects/anav', 'anav'],
  ['/lab/skynet', 'skynet'],
]) {
  await page.goto(base + route, { waitUntil: 'commit' });
  await page.waitForTimeout(350);
  await shot(`${name}-a-arriving`);
  await page.waitForTimeout(2200);
  await shot(`${name}-b-settled`);
}

// Briefing: the identity card handed over, then still.
await page.goto(base + '/briefing', { waitUntil: 'commit' });
await page.waitForTimeout(450);
await shot('briefing-a-handoff');
await page.waitForTimeout(1600);
await shot('briefing-b-settled');

// Home: the Saarthi plate mid-scan and at rest.
await page.goto(base + '/', { waitUntil: 'load' });
await page.waitForTimeout(1200);
await page.evaluate(() => {
  const p = document.querySelector('.plate__frame');
  window.scrollTo(0, p.getBoundingClientRect().top + scrollY - innerHeight * 0.8);
});
await page.waitForTimeout(500);
await shot('plate-a-entering');
await page.evaluate(() => window.scrollBy(0, innerHeight * 0.5));
await page.waitForTimeout(500);
await shot('plate-b-rest');

// Home: hero boot, then a record scanning in.
await page.goto(base + '/', { waitUntil: 'commit' });
await page.waitForTimeout(900);
await shot('home-a-boot');
await page.waitForTimeout(2600);
await shot('home-b-booted');
await page.evaluate(() => {
  const r = document.querySelector('.rec--anav');
  window.scrollTo(0, r.getBoundingClientRect().top + scrollY - innerHeight * 0.75);
});
await page.waitForTimeout(600);
await shot('home-c-record-entering');
await page.evaluate(() => window.scrollBy(0, innerHeight * 0.45));
await page.waitForTimeout(600);
await shot('home-d-record-in');

console.log(errors.length ? `page errors: ${errors.join(' | ')}` : 'no page errors');
await browser.close();
