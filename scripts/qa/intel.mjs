// The briefing's opening (BriefingIntel.astro): screenshots through its timeline, desktop and phone,
// then checks that it hands over to the page (card in place, focus on the name, overlay gone).
// Usage: node scripts/qa/intel.mjs [outdir]   (needs the preview on http://127.0.0.1:8787)
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const BASE = process.env.BASE ?? 'http://127.0.0.1:8787';
const out = process.argv[2] ?? 'qa/intel';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge' });
let fails = 0;
const report = (ok, msg) => {
  if (!ok) fails++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${msg}`);
};

for (const [name, viewport] of [
  ['desk', { width: 1440, height: 900 }],
  ['phone', { width: 390, height: 844 }],
]) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  await ctx.addInitScript(() => sessionStorage.setItem('intro-seen', '1'));
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(BASE + '/briefing', { waitUntil: 'load' });
  report(await page.locator('[data-intel]').isVisible(), `${name}: the briefing opens on the feed`);
  const t0 = Date.now();
  for (const at of [0.3, 1.6, 3.0, 4.3, 5.4, 6.8]) {
    const wait = at * 1000 - (Date.now() - t0);
    if (wait > 0) await page.waitForTimeout(wait);
    await page.screenshot({ path: `${out}/${name}-${String(at).replace('.', '_')}s.png` });
  }
  await page.waitForSelector('[data-intel]', { state: 'hidden', timeout: 6000 });
  await page.waitForTimeout(300);
  report(
    (await page.evaluate(() => document.activeElement?.id)) === 'brief-name',
    `${name}: it hands over to the page, focus on the name`,
  );
  const card = await page.locator('[data-idcard]').boundingBox();
  report(card && card.y < viewport.height, `${name}: the card is in its place`);
  await page.screenshot({ path: `${out}/${name}-after.png` });
  report(errors.length === 0, `${name}: no page errors ${errors.join(' | ')}`);
  await ctx.close();
}

// Skip at once: straight to the page.
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem('intro-seen', '1'));
  const page = await ctx.newPage();
  await page.goto(BASE + '/briefing', { waitUntil: 'load' });
  await page.keyboard.press('Escape');
  await page.waitForSelector('[data-intel]', { state: 'hidden', timeout: 2000 });
  const op = await page.locator('[data-idcard]').evaluate((e) => getComputedStyle(e).opacity);
  report(op === '1', 'Escape: the page at once, the card shown');
  await ctx.close();
}
await browser.close();
process.exit(fails ? 1 : 0);
