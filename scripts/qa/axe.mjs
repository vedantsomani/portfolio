// Check 6: axe-core on every route (and the 404) at 375 and 1440 px.
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { BASE, NOT_FOUND, ROUTES } from './routes.mjs';

const browser = await chromium.launch({ channel: 'msedge' });
let ok = true;
for (const width of [375, 1440]) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  const page = await context.newPage();
  for (const route of [...ROUTES, NOT_FOUND]) {
    await page.goto(BASE + route, { waitUntil: 'networkidle' });
    // Let the hall mount and the hero reveal finish, so the scan sees the live DOM.
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1500);
    await page.evaluate(() => window.scrollTo(0, 0));
    const { violations } = await new AxeBuilder({ page }).analyze();
    ok &&= violations.length === 0;
    const detail = violations.map((v) => `${v.id} ×${v.nodes.length}: ${v.nodes[0]?.target}`);
    console.log(
      `${String(width).padStart(4)}  ${route.padEnd(28)} ${violations.length} violations${detail.length ? '  ' + detail.join('; ') : ''}`,
    );
  }
  await context.close();
}
await browser.close();
if (!ok) process.exit(1);
