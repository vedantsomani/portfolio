// Viewport captures at successive scroll positions (what a visitor sees, not a full-page stitch).
// Usage: node scripts/qa/frames.mjs <base> <outDir> <route,route> <width,width> [steps]
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
const [,, base, out, routesArg, widthsArg, stepsArg] = process.argv;
const routes = routesArg.split(',');
const widths = widthsArg.split(',').map(Number);
const steps = Number(stepsArg ?? 8);
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge' });
for (const w of widths) {
  const h = w < 600 ? 812 : 900;
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  await ctx.addInitScript(() => { try { sessionStorage.setItem('intro-seen', '1'); } catch { /* storage blocked: the gate shows */ } });
  const page = await ctx.newPage();
  for (const r of routes) {
    await page.goto(base + r, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    const total = await page.evaluate(() => document.body.scrollHeight);
    const name = r === '/' ? 'home' : r.replace(/\//g, '_').replace(/^_/, '');
    for (let i = 0; i < steps; i++) {
      const y = Math.round((total - h) * (i / Math.max(1, steps - 1)));
      await page.evaluate((y) => window.scrollTo(0, y), y);
      await page.waitForTimeout(700);
      await page.screenshot({ path: `${out}/${name}-${w}-${i}.jpg`, quality: 60, type: 'jpeg' });
    }
  }
  await ctx.close();
}
await browser.close();
